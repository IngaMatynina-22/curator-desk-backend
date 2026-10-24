from __future__ import annotations

from sqlalchemy import func, or_, select

from app.core.enums import StudentStatus
from app.models.academic_group import AcademicGroup
from app.models.student import Student
from app.repositories.base import BaseRepository
from app.schemas.group import GroupFilter


class GroupRepository(BaseRepository[AcademicGroup]):
    model = AcademicGroup

    def search(self, filters: GroupFilter) -> tuple[list[AcademicGroup], int]:
        stmt = select(AcademicGroup)
        if not filters.include_archived:
            stmt = stmt.where(AcademicGroup.is_archived.is_(False))
        if filters.query:
            q = f"%{filters.query}%"
            stmt = stmt.where(
                or_(AcademicGroup.name.ilike(q), AcademicGroup.specialty.ilike(q))
            )
        if filters.academic_year:
            stmt = stmt.where(AcademicGroup.academic_year == filters.academic_year)
        if filters.course is not None:
            stmt = stmt.where(AcademicGroup.course == filters.course)
        stmt = stmt.order_by(AcademicGroup.name)
        return self.paginate(stmt, offset=filters.offset, limit=filters.limit)

    def count_active_students(self, group_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Student)
            .where(
                Student.group_id == group_id,
                Student.is_archived.is_(False),
                Student.status == StudentStatus.ACTIVE,
            )
        )
        return int(self.session.scalar(stmt) or 0)
