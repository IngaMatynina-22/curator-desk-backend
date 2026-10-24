from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import CuratorLogCategory
from app.database.base import Base
from app.models.associations import CuratorLogStudent
from app.models.mixins import TimestampMixin


class CuratorLog(Base, TimestampMixin):
    __tablename__ = "curator_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    category: Mapped[str] = mapped_column(
        String(64), nullable=False, default=CuratorLogCategory.OTHER, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True
    )
    meeting_id: Mapped[int | None] = mapped_column(
        ForeignKey("meetings.id", ondelete="SET NULL"), nullable=True, index=True
    )

    student_links: Mapped[list[CuratorLogStudent]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def student_ids(self) -> list[int]:
        return [link.student_id for link in self.student_links]
