from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import StudentStatus, StudyForm
from app.database.base import Base
from app.models.mixins import SoftArchiveMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.academic_group import AcademicGroup
    from app.models.academic_record import AcademicRecord
    from app.models.attendance import AttendanceRecord
    from app.models.note import Note


class Student(Base, TimestampMixin, SoftArchiveMixin):
    __tablename__ = "students"
    __table_args__ = (UniqueConstraint("student_number", name="uq_students_student_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    middle_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emergency_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    personal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    group_id: Mapped[int] = mapped_column(
        ForeignKey("academic_groups.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    enrollment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=StudentStatus.ACTIVE, index=True
    )
    study_form: Mapped[str] = mapped_column(
        String(32), nullable=False, default=StudyForm.FULL_TIME
    )
    course: Mapped[int | None] = mapped_column(Integer, nullable=True)
    specialty: Mapped[str | None] = mapped_column(String(255), nullable=True)
    academic_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    group: Mapped[AcademicGroup] = relationship(back_populates="students")
    academic_records: Mapped[list[AcademicRecord]] = relationship(back_populates="student")
    attendance_records: Mapped[list[AttendanceRecord]] = relationship(back_populates="student")
    notes: Mapped[list[Note]] = relationship(back_populates="student")

    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)
