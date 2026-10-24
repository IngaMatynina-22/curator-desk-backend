from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.mixins import SoftArchiveMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.student import Student


class AcademicGroup(Base, TimestampMixin, SoftArchiveMixin):
    __tablename__ = "academic_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    specialty: Mapped[str] = mapped_column(String(255), nullable=False)
    course: Mapped[int] = mapped_column(Integer, nullable=False)
    academic_year: Mapped[str] = mapped_column(String(32), nullable=False)
    curator_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    students: Mapped[list[Student]] = relationship(back_populates="group")
