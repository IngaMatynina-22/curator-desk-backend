from __future__ import annotations

from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    model = AuditLog

    def for_entity(self, entity_type: str, entity_id: int) -> list[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
            .order_by(AuditLog.occurred_at.desc())
        )
        return list(self.session.scalars(stmt).all())

    def recent(self, limit: int = 100) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.occurred_at.desc()).limit(limit)
        return list(self.session.scalars(stmt).all())
