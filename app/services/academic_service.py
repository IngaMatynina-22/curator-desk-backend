from __future__ import annotations

from pydantic import ValidationError as PydanticValidationError

from app.core.enums import AuditOperation, GradeScale
from app.core.exceptions import ConflictError, ValidationError
from app.models.academic_record import AcademicRecord
from app.models.subject import Subject
from app.repositories.academic_record_repository import (
    AcademicRecordRepository,
    SubjectRepository,
)
from app.repositories.student_repository import StudentRepository
from app.schemas.academic_record import (
    AcademicRecordCreate,
    AcademicRecordFilter,
    AcademicRecordOut,
    AcademicRecordUpdate,
    SubjectCreate,
    SubjectOut,
    SubjectUpdate,
)
from app.schemas.common import PageResult
from app.services.base import BaseService


class AcademicService(BaseService):
    entity_type = "academic_record"

    def __init__(self, session):
        super().__init__(session)
        self.records = AcademicRecordRepository(session)
        self.subjects = SubjectRepository(session)
        self.students = StudentRepository(session)

    def create_subject(self, data: SubjectCreate | dict) -> SubjectOut:
        payload = self._parse(SubjectCreate, data)
        if self.subjects.get_by_name(payload.name):
            raise ConflictError(f"subject already exists: {payload.name}")
        subject = Subject(**payload.model_dump())
        self.subjects.add(subject)
        self.commit()
        return SubjectOut.model_validate(subject)

    def update_subject(self, subject_id: int, data: SubjectUpdate | dict) -> SubjectOut:
        payload = self._parse(SubjectUpdate, data)
        subject = self.subjects.get_or_raise(subject_id, "Subject")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(subject, key, value)
        self.flush()
        self.commit()
        return SubjectOut.model_validate(subject)

    def list_subjects(self, include_archived: bool = False) -> list[SubjectOut]:
        items = self.subjects.list(include_archived=include_archived, order_by=Subject.name)
        return [SubjectOut.model_validate(s) for s in items]

    def create_record(self, data: AcademicRecordCreate | dict) -> AcademicRecordOut:
        payload = self._parse(AcademicRecordCreate, data)
        self.students.get_or_raise(payload.student_id, "Student")
        self.subjects.get_or_raise(payload.subject_id, "Subject")
        record = AcademicRecord(**payload.model_dump())
        self.records.add(record)
        self.audit(record.id, AuditOperation.CREATE)
        self.commit()
        return AcademicRecordOut.model_validate(record)

    def update_record(self, record_id: int, data: AcademicRecordUpdate | dict) -> AcademicRecordOut:
        payload = self._parse(AcademicRecordUpdate, data)
        record = self.records.get_or_raise(record_id, "AcademicRecord")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(record, key, value)
        self.flush()
        self.audit(record.id, AuditOperation.UPDATE)
        self.commit()
        return AcademicRecordOut.model_validate(record)

    def list_records(
        self, filters: AcademicRecordFilter | dict | None = None
    ) -> PageResult[AcademicRecordOut]:
        f = self._parse(AcademicRecordFilter, filters or {})
        items, total = self.records.search(f)
        return PageResult(
            items=[AcademicRecordOut.model_validate(r) for r in items],
            total=total,
            offset=f.offset,
            limit=f.limit,
        )

    def average_for_student(self, student_id: int) -> float | None:
        self.students.get_or_raise(student_id, "Student")
        return self.records.average_score(student_id, GradeScale.NUMERIC)

    @staticmethod
    def _parse(model, data):
        try:
            if isinstance(data, model):
                return data
            return model.model_validate(data)
        except PydanticValidationError as exc:
            raise ValidationError(str(exc)) from exc
