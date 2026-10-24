from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import NotificationKind, NotificationStatus
from app.schemas.common import ORMModel


class NotificationOut(ORMModel):
    id: int
    kind: str
    source_type: str
    source_id: int
    title: str
    body: str | None
    due_at: datetime | None
    status: str
    snoozed_until: datetime | None
    created_at: datetime


class ReminderSettings(BaseModel):
    event_hours_before: int = Field(24, ge=0)
    meeting_hours_before: int = Field(24, ge=0)
    duty_hours_before: int = Field(12, ge=0)
    assignment_hours_before: int = Field(48, ge=0)
    check_missing_attendance: bool = True


class SnoozeRequest(BaseModel):
    until: datetime
