from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import MeetingFormat, MeetingStatus
from app.database.base import Base
from app.models.associations import MeetingStudent
from app.models.mixins import TimestampMixin


class Meeting(Base, TimestampMixin):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    format: Mapped[str] = mapped_column(
        String(32), nullable=False, default=MeetingFormat.INDIVIDUAL
    )
    topic: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_steps: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_contact_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=MeetingStatus.PLANNED, index=True
    )

    student_links: Mapped[list[MeetingStudent]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def student_ids(self) -> list[int]:
        return [link.student_id for link in self.student_links]
