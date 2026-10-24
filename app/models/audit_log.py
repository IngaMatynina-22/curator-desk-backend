from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.date_utils import utc_now
from app.core.enums import AuditOperation
from app.database.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    operation: Mapped[str] = mapped_column(
        String(32), nullable=False, default=AuditOperation.CREATE, index=True
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, index=True
    )
    operator_name: Mapped[str] = mapped_column(String(128), nullable=False, default="curator")
    changed_fields: Mapped[str | None] = mapped_column(Text, nullable=True)
