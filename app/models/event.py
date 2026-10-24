from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import EventStatus, EventType
from app.database.base import Base
from app.models.associations import EventStudent
from app.models.mixins import TimestampMixin


class Event(Base, TimestampMixin):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("ends_at >= starts_at", name="ck_events_end_after_start"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default=EventType.OTHER, index=True
    )
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=EventStatus.PLANNED, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recurrence_group_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    student_links: Mapped[list[EventStudent]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def participant_ids(self) -> list[int]:
        from app.core.enums import EventStudentRole

        return [
            link.student_id
            for link in self.student_links
            if link.role == EventStudentRole.PARTICIPANT
        ]

    @property
    def responsible_ids(self) -> list[int]:
        from app.core.enums import EventStudentRole

        return [
            link.student_id
            for link in self.student_links
            if link.role == EventStudentRole.RESPONSIBLE
        ]
