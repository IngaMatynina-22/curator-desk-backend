from __future__ import annotations

from pydantic import ValidationError as PydanticValidationError

from app.core.date_utils import utc_now
from app.core.enums import AttendanceStatus, AuditOperation
from app.core.exceptions import ConflictError, ValidationError
from app.models.attendance import AttendanceRecord, Lesson
from app.repositories.attendance_repository import AttendanceRepository, LessonRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.academic_record_repository import SubjectRepository
from app.schemas.attendance import (
    AbsenceStats,
    AttendanceCreate,
    AttendanceFilter,
    AttendanceMark,
    AttendanceOut,
    AttendanceUpdate,
    BulkAttendanceCreate,
    LessonCreate,
    LessonOut,
)
from app.schemas.common import PageResult
from app.services.audit_hooks import diff_fields
from app.services.base import BaseService


class AttendanceService(BaseService):
    entity_type = "attendance_record"

    def __init__(self, session):
        super().__init__(session)
        self.lessons = LessonRepository(session)
        self.attendance = AttendanceRepository(session)
        self.students = StudentRepository(session)
        self.subjects = SubjectRepository(session)

    def create_lesson(self, data: LessonCreate | dict) -> LessonOut:
        payload = self._parse(LessonCreate, data)
        self.subjects.get_or_raise(payload.subject_id, "Subject")
        lesson = Lesson(**payload.model_dump())
        self.lessons.add(lesson)
        self.commit()
        return LessonOut.model_validate(lesson)

    def get_lesson(self, lesson_id: int) -> LessonOut:
        return LessonOut.model_validate(self.lessons.get_or_raise(lesson_id, "Lesson"))

    def mark(self, data: AttendanceCreate | dict) -> AttendanceOut:
        payload = self._parse(AttendanceCreate, data)
        return self._upsert_mark(payload.lesson_id, payload)

    def bulk_mark(self, data: BulkAttendanceCreate | dict) -> list[AttendanceOut]:
        payload = self._parse(BulkAttendanceCreate, data)
        self.lessons.get_or_raise(payload.lesson_id, "Lesson")
        results = []
        for mark in payload.marks:
            results.append(self._upsert_mark(payload.lesson_id, mark, commit=False))
        self.commit()
        return results

    def update(self, record_id: int, data: AttendanceUpdate | dict) -> AttendanceOut:
        payload = self._parse(AttendanceUpdate, data)
        record = self.attendance.get_or_raise(record_id, "AttendanceRecord")
        values = payload.model_dump(exclude_unset=True)
        old = {k: getattr(record, k) for k in values}
        for key, value in values.items():
            setattr(record, key, value)
        self._normalize_hours(record)
        self.flush()
        self.audit(record.id, AuditOperation.UPDATE, diff_fields(old, {**old, **values}))
        self.commit()
        return AttendanceOut.model_validate(record)

    def list(self, filters: AttendanceFilter | dict | None = None) -> PageResult[AttendanceOut]:
        f = self._parse(AttendanceFilter, filters or {})
        items, total = self.attendance.search(f)
        return PageResult(
            items=[AttendanceOut.model_validate(r) for r in items],
            total=total,
            offset=f.offset,
            limit=f.limit,
        )

    def student_stats(self, student_id: int, date_from=None, date_to=None) -> AbsenceStats:
        self.students.get_or_raise(student_id, "Student")
        return AbsenceStats(**self.attendance.absence_stats(student_id, date_from, date_to))

    def top_absentees(self, limit: int = 10, date_from=None, date_to=None):
        return self.attendance.top_absentees(limit=limit, date_from=date_from, date_to=date_to)

    def _upsert_mark(
        self, lesson_id: int, mark: AttendanceMark | AttendanceCreate, *, commit: bool = True
    ) -> AttendanceOut:
        self.lessons.get_or_raise(lesson_id, "Lesson")
        self.students.get_or_raise(mark.student_id, "Student")
        existing = self.attendance.get_for_lesson_student(lesson_id, mark.student_id)
        data = mark.model_dump()
        data.pop("lesson_id", None)
        if existing:
            raise ConflictError(
                f"attendance already exists for student={mark.student_id} lesson={lesson_id}"
            )
        record = AttendanceRecord(
            lesson_id=lesson_id,
            recorded_at=utc_now(),
            **data,
        )
        self._normalize_hours(record)
        self.attendance.add(record)
        self.audit(record.id, AuditOperation.CREATE)
        if commit:
            self.commit()
        else:
            self.flush()
        return AttendanceOut.model_validate(record)

    @staticmethod
    def _normalize_hours(record: AttendanceRecord) -> None:
        if record.status == AttendanceStatus.PRESENT:
            record.hours_missed = 0.0
        elif record.status in {AttendanceStatus.ABSENT, AttendanceStatus.EXCUSED}:
            if record.hours_missed <= 0:
                record.hours_missed = 2.0

    @staticmethod
    def _parse(model, data):
        try:
            if isinstance(data, model):
                return data
            return model.model_validate(data)
        except PydanticValidationError as exc:
            raise ValidationError(str(exc)) from exc
