from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import AssignmentPriority, AssignmentStatus
from app.database.base import Base
from app.models.associations import AssignmentStudent
from app.models.mixins import TimestampMixin


class Assignment(Base, TimestampMixin):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    priority: Mapped[str] = mapped_column(
        String(32), nullable=False, default=AssignmentPriority.MEDIUM, index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=AssignmentStatus.NEW, index=True
    )
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    result_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    student_links: Mapped[list[AssignmentStudent]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def student_ids(self) -> list[int]:
        return [link.student_id for link in self.student_links]

    @property
    def is_overdue(self) -> bool:
        if self.status in {AssignmentStatus.DONE, AssignmentStatus.CANCELLED}:
            return False
        return self.due_date < date.today()

    @property
    def effective_status(self) -> str:
        if self.is_overdue:
            return "overdue"
        return self.status
