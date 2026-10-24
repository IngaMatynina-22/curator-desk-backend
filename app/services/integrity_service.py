from __future__ import annotations

from sqlalchemy import func, select, text

from app.models.academic_group import AcademicGroup
from app.models.associations import (
    AssignmentStudent,
    DutyStudent,
    EventStudent,
    MeetingStudent,
)
from app.models.attendance import AttendanceRecord, Lesson
from app.models.event import Event
from app.models.student import Student
from app.schemas.integrity import IntegrityIssue, IntegrityReport
from app.services.base import BaseService


class IntegrityService(BaseService):
    def run_checks(self) -> IntegrityReport:
        issues: list[IntegrityIssue] = []
        issues.extend(self._duplicate_student_numbers())
        issues.extend(self._orphaned_m2m())
        issues.extend(self._attendance_without_lesson())
        issues.extend(self._invalid_event_ranges())
        issues.extend(self._archived_group_active_students())
        issues.extend(self._empty_required_names())
        return IntegrityReport(ok=len(issues) == 0, issues=issues)

    def _duplicate_student_numbers(self) -> list[IntegrityIssue]:
        rows = self.session.execute(
            select(Student.student_number, func.count())
            .group_by(Student.student_number)
            .having(func.count() > 1)
        ).all()
        return [
            IntegrityIssue(
                code="duplicate_student_number",
                severity="error",
                message=f"Duplicate student_number={num} count={cnt}",
            )
            for num, cnt in rows
        ]

    def _orphaned_m2m(self) -> list[IntegrityIssue]:
        issues = []
        for model, label in [
            (AssignmentStudent, "assignment_students"),
            (DutyStudent, "duty_students"),
            (EventStudent, "event_students"),
            (MeetingStudent, "meeting_students"),
        ]:
            stmt = select(model).where(
                ~model.student_id.in_(select(Student.id))
            )
            for row in self.session.scalars(stmt):
                issues.append(
                    IntegrityIssue(
                        code="orphan_m2m",
                        severity="error",
                        message=f"Orphan link in {label} id={row.id}",
                        entity_type=label,
                        entity_id=row.id,
                    )
                )
        return issues

    def _attendance_without_lesson(self) -> list[IntegrityIssue]:
        stmt = select(AttendanceRecord).where(
            ~AttendanceRecord.lesson_id.in_(select(Lesson.id))
        )
        return [
            IntegrityIssue(
                code="attendance_missing_lesson",
                severity="error",
                message=f"Attendance {r.id} references missing lesson",
                entity_type="attendance_record",
                entity_id=r.id,
            )
            for r in self.session.scalars(stmt)
        ]

    def _invalid_event_ranges(self) -> list[IntegrityIssue]:
        # CHECK usually prevents this; still report if any slip through.
        stmt = select(Event).where(Event.ends_at < Event.starts_at)
        return [
            IntegrityIssue(
                code="event_invalid_range",
                severity="error",
                message=f"Event {e.id} ends before it starts",
                entity_type="event",
                entity_id=e.id,
            )
            for e in self.session.scalars(stmt)
        ]

    def _archived_group_active_students(self) -> list[IntegrityIssue]:
        stmt = (
            select(Student)
            .join(AcademicGroup)
            .where(
                AcademicGroup.is_archived.is_(True),
                Student.is_archived.is_(False),
                Student.status == "active",
            )
        )
        return [
            IntegrityIssue(
                code="active_student_in_archived_group",
                severity="warning",
                message=f"Active student {s.id} in archived group {s.group_id}",
                entity_type="student",
                entity_id=s.id,
            )
            for s in self.session.scalars(stmt)
        ]

    def _empty_required_names(self) -> list[IntegrityIssue]:
        stmt = select(Student).where(
            (Student.last_name == "") | (Student.first_name == "") | (Student.student_number == "")
        )
        return [
            IntegrityIssue(
                code="empty_required_field",
                severity="error",
                message=f"Student {s.id} has empty required field",
                entity_type="student",
                entity_id=s.id,
            )
            for s in self.session.scalars(stmt)
        ]
