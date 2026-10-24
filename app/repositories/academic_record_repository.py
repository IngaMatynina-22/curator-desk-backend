from __future__ import annotations

from sqlalchemy import func, select

from app.core.enums import GradeScale
from app.models.academic_record import AcademicRecord
from app.models.subject import Subject
from app.repositories.base import BaseRepository
from app.schemas.academic_record import AcademicRecordFilter


class SubjectRepository(BaseRepository[Subject]):
    model = Subject

    def get_by_name(self, name: str) -> Subject | None:
        return self.session.scalar(select(Subject).where(Subject.name == name))


class AcademicRecordRepository(BaseRepository[AcademicRecord]):
    model = AcademicRecord

    def search(self, filters: AcademicRecordFilter) -> tuple[list[AcademicRecord], int]:
        stmt = select(AcademicRecord)
        if filters.student_id is not None:
            stmt = stmt.where(AcademicRecord.student_id == filters.student_id)
        if filters.subject_id is not None:
            stmt = stmt.where(AcademicRecord.subject_id == filters.subject_id)
        if filters.grade_scale is not None:
            stmt = stmt.where(AcademicRecord.grade_scale == filters.grade_scale)
        if filters.date_from is not None:
            stmt = stmt.where(AcademicRecord.record_date >= filters.date_from)
        if filters.date_to is not None:
            stmt = stmt.where(AcademicRecord.record_date <= filters.date_to)
        stmt = stmt.order_by(AcademicRecord.record_date.desc())
        return self.paginate(stmt, offset=filters.offset, limit=filters.limit)

    def average_score(self, student_id: int, grade_scale: GradeScale = GradeScale.NUMERIC) -> float | None:
        stmt = select(func.avg(AcademicRecord.score)).where(
            AcademicRecord.student_id == student_id,
            AcademicRecord.grade_scale == grade_scale,
            AcademicRecord.score.is_not(None),
        )
        value = self.session.scalar(stmt)
        return float(value) if value is not None else None
