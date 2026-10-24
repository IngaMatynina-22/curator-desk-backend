from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.mixins import SoftArchiveMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.academic_record import AcademicRecord
    from app.models.attendance import Lesson


class Subject(Base, TimestampMixin, SoftArchiveMixin):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    academic_records: Mapped[list[AcademicRecord]] = relationship(back_populates="subject")
    lessons: Mapped[list[Lesson]] = relationship(back_populates="subject")
