from __future__ import annotations

from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import func, select

from app.core.date_utils import ensure_not_future
from app.core.enums import AssignmentStatus, AttendanceStatus, AuditOperation
from app.core.exceptions import ConflictError, ValidationError
from app.models.assignment import Assignment
from app.models.associations import AssignmentStudent, EventStudent, MeetingStudent
from app.models.attendance import AttendanceRecord
from app.models.event import Event
from app.models.meeting import Meeting
from app.models.student import Student
from app.repositories.group_repository import GroupRepository
from app.repositories.student_repository import StudentRepository
from app.schemas.common import PageResult
from app.schemas.student import (
    StudentCreate,
    StudentFilter,
    StudentOut,
    StudentSummary,
    StudentUpdate,
)
from app.services.audit_hooks import diff_fields
from app.services.base import BaseService


class StudentService(BaseService):
    entity_type = "student"

    def __init__(self, session):
        super().__init__(session)
        self.repo = StudentRepository(session)
        self.groups = GroupRepository(session)

    def create(self, data: StudentCreate | dict) -> StudentOut:
        payload = self._parse(StudentCreate, data)
        if payload.birth_date:
            ensure_not_future(payload.birth_date, "birth_date")
        self.groups.get_or_raise(payload.group_id, "Group")
        if self.repo.get_by_number(payload.student_number):
            raise ConflictError(f"student_number already exists: {payload.student_number}")
        student = Student(**payload.model_dump())
        self.repo.add(student)
        self.audit(student.id, AuditOperation.CREATE, {"student_number": student.student_number})
        self.commit()
        return self._to_out(student)

    def update(self, student_id: int, data: StudentUpdate | dict) -> StudentOut:
        payload = self._parse(StudentUpdate, data)
        student = self.repo.get_or_raise(student_id, "Student")
        values = payload.model_dump(exclude_unset=True)
        if "birth_date" in values and values["birth_date"]:
            ensure_not_future(values["birth_date"], "birth_date")
        if "group_id" in values:
            self.groups.get_or_raise(values["group_id"], "Group")
        if "student_number" in values:
            existing = self.repo.get_by_number(values["student_number"])
            if existing and existing.id != student_id:
                raise ConflictError("student_number already exists")
        old = {k: getattr(student, k) for k in values}
        for key, value in values.items():
            setattr(student, key, value)
        self.flush()
        self.audit(student.id, AuditOperation.UPDATE, diff_fields(old, values))
        self.commit()
        return self._to_out(student)

    def get(self, student_id: int) -> StudentOut:
        return self._to_out(self.repo.get_or_raise(student_id, "Student"))

    def list(self, filters: StudentFilter | dict | None = None) -> PageResult[StudentOut]:
        f = self._parse(StudentFilter, filters or {})
        items, total = self.repo.search(f)
        return PageResult(
            items=[self._to_out(s) for s in items],
            total=total,
            offset=f.offset,
            limit=f.limit,
        )

    def archive(self, student_id: int) -> StudentOut:
        student = self.repo.get_or_raise(student_id, "Student")
        self.repo.archive(student)
        self.audit(student.id, AuditOperation.ARCHIVE)
        self.commit()
        return self._to_out(student)

    def restore(self, student_id: int) -> StudentOut:
        student = self.repo.get_or_raise(student_id, "Student")
        self.repo.restore(student)
        self.audit(student.id, AuditOperation.RESTORE)
        self.commit()
        return self._to_out(student)

    def summary(self, student_id: int) -> StudentSummary:
        student = self.repo.get_or_raise(student_id, "Student")
        absences = int(
            self.session.scalar(
                select(func.count()).where(
                    AttendanceRecord.student_id == student_id,
                    AttendanceRecord.status == AttendanceStatus.ABSENT,
                )
            )
            or 0
        )
        excused = int(
            self.session.scalar(
                select(func.count()).where(
                    AttendanceRecord.student_id == student_id,
                    AttendanceRecord.status == AttendanceStatus.EXCUSED,
                )
            )
            or 0
        )
        open_assignments = int(
            self.session.scalar(
                select(func.count())
                .select_from(AssignmentStudent)
                .join(Assignment)
                .where(
                    AssignmentStudent.student_id == student_id,
                    Assignment.status.in_(
                        [AssignmentStatus.NEW, AssignmentStatus.IN_PROGRESS]
                    ),
                )
            )
            or 0
        )
        events_count = int(
            self.session.scalar(
                select(func.count()).where(EventStudent.student_id == student_id)
            )
            or 0
        )
        meetings_count = int(
            self.session.scalar(
                select(func.count()).where(MeetingStudent.student_id == student_id)
            )
            or 0
        )
        return StudentSummary(
            student=self._to_out(student),
            attendance_absences=absences,
            attendance_excused=excused,
            open_assignments=open_assignments,
            events_count=events_count,
            meetings_count=meetings_count,
        )

    def _to_out(self, student: Student) -> StudentOut:
        out = StudentOut.model_validate(student)
        out.full_name = student.full_name
        return out

    @staticmethod
    def _parse(model, data):
        try:
            if isinstance(data, model):
                return data
            return model.model_validate(data)
        except PydanticValidationError as exc:
            raise ValidationError(str(exc)) from exc
