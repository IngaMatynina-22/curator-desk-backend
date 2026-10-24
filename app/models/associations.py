"""Many-to-many association tables / models."""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import EventStudentRole
from app.database.base import Base


class DutyStudent(Base):
    __tablename__ = "duty_students"
    __table_args__ = (UniqueConstraint("duty_id", "student_id", name="uq_duty_student"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    duty_id: Mapped[int] = mapped_column(
        ForeignKey("duties.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True
    )


class AssignmentStudent(Base):
    __tablename__ = "assignment_students"
    __table_args__ = (
        UniqueConstraint("assignment_id", "student_id", name="uq_assignment_student"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True
    )


class EventStudent(Base):
    __tablename__ = "event_students"
    __table_args__ = (
        UniqueConstraint("event_id", "student_id", "role", name="uq_event_student_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(
        String(32), nullable=False, default=EventStudentRole.PARTICIPANT
    )


class MeetingStudent(Base):
    __tablename__ = "meeting_students"
    __table_args__ = (UniqueConstraint("meeting_id", "student_id", name="uq_meeting_student"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True
    )


class CuratorLogStudent(Base):
    __tablename__ = "curator_log_students"
    __table_args__ = (
        UniqueConstraint("curator_log_id", "student_id", name="uq_curator_log_student"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    curator_log_id: Mapped[int] = mapped_column(
        ForeignKey("curator_logs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True
    )
