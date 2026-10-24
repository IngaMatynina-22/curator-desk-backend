from __future__ import annotations

import json

from app.models.app_setting import AppSetting
from app.schemas.notification import ReminderSettings
from app.services.base import BaseService
from sqlalchemy import select


DEFAULT_SETTINGS = {
    "reminder": ReminderSettings().model_dump(),
    "export_format": "csv",
    "date_format": "%Y-%m-%d",
}


class SettingsService(BaseService):
    entity_type = "app_setting"

    def get(self, key: str, default=None):
        row = self.session.scalar(select(AppSetting).where(AppSetting.key == key))
        if row is None:
            return DEFAULT_SETTINGS.get(key, default)
        try:
            return json.loads(row.value_json)
        except json.JSONDecodeError:
            return default

    def set(self, key: str, value) -> None:
        row = self.session.scalar(select(AppSetting).where(AppSetting.key == key))
        payload = json.dumps(value, ensure_ascii=False, default=str)
        if row is None:
            self.session.add(AppSetting(key=key, value_json=payload))
        else:
            row.value_json = payload
        self.commit()

    def get_reminder_settings(self) -> ReminderSettings:
        data = self.get("reminder") or {}
        return ReminderSettings.model_validate(data)

    def set_reminder_settings(self, data: ReminderSettings | dict) -> ReminderSettings:
        if isinstance(data, ReminderSettings):
            payload = data
        else:
            payload = ReminderSettings.model_validate(data)
        self.set("reminder", payload.model_dump())
        return payload

    def all(self) -> dict:
        result = dict(DEFAULT_SETTINGS)
        for row in self.session.scalars(select(AppSetting)):
            try:
                result[row.key] = json.loads(row.value_json)
            except json.JSONDecodeError:
                result[row.key] = row.value_json
        return result
