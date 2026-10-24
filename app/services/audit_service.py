from __future__ import annotations

import json
from datetime import datetime

from pydantic import BaseModel

from app.repositories.audit_repository import AuditRepository
from app.services.base import BaseService


class AuditOut(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    operation: str
    occurred_at: datetime
    operator_name: str
    changed_fields: dict | list | None = None


class AuditService(BaseService):
    entity_type = "audit_log"

    def __init__(self, session):
        super().__init__(session)
        self.repo = AuditRepository(session)

    def for_entity(self, entity_type: str, entity_id: int) -> list[AuditOut]:
        return [self._to_out(e) for e in self.repo.for_entity(entity_type, entity_id)]

    def recent(self, limit: int = 100) -> list[AuditOut]:
        return [self._to_out(e) for e in self.repo.recent(limit=limit)]

    def diff_view(self, entity_type: str, entity_id: int) -> list[dict]:
        """Ordered field-level change history for an entity."""
        rows = []
        for entry in self.for_entity(entity_type, entity_id):
            if not entry.changed_fields or not isinstance(entry.changed_fields, dict):
                continue
            for field, change in entry.changed_fields.items():
                if isinstance(change, dict) and ("old" in change or "new" in change):
                    rows.append(
                        {
                            "occurred_at": entry.occurred_at,
                            "operation": entry.operation,
                            "field": field,
                            "old": change.get("old"),
                            "new": change.get("new"),
                            "audit_id": entry.id,
                        }
                    )
                else:
                    rows.append(
                        {
                            "occurred_at": entry.occurred_at,
                            "operation": entry.operation,
                            "field": field,
                            "old": None,
                            "new": change,
                            "audit_id": entry.id,
                        }
                    )
        rows.sort(key=lambda r: r["occurred_at"])
        return rows

    @staticmethod
    def _to_out(entry) -> AuditOut:
        changes = None
        if entry.changed_fields:
            try:
                changes = json.loads(entry.changed_fields)
            except json.JSONDecodeError:
                changes = {"raw": entry.changed_fields}
        return AuditOut(
            id=entry.id,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            operation=entry.operation,
            occurred_at=entry.occurred_at,
            operator_name=entry.operator_name,
            changed_fields=changes,
        )
