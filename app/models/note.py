from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import NoteCategory
from app.database.base import Base
from app.models.mixins import SoftArchiveMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.student import Student


class Note(Base, TimestampMixin, SoftArchiveMixin):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(32), nullable=False, default=NoteCategory.GENERAL, index=True
    )
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    student_id: Mapped[int | None] = mapped_column(
        ForeignKey("students.id", ondelete="SET NULL"), nullable=True, index=True
    )
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("academic_groups.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True
    )
    assignment_id: Mapped[int | None] = mapped_column(
        ForeignKey("assignments.id", ondelete="SET NULL"), nullable=True, index=True
    )

    student: Mapped[Student | None] = relationship(back_populates="notes")
