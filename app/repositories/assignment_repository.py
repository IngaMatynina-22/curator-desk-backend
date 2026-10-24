from __future__ import annotations

from sqlalchemy import select

from datetime import date

from app.core.enums import AssignmentStatus
from app.models.assignment import Assignment
from app.models.associations import AssignmentStudent
from app.repositories.base import BaseRepository
from app.schemas.assignment import AssignmentFilter


class AssignmentRepository(BaseRepository[Assignment]):
    model = Assignment

    def search(self, filters: AssignmentFilter) -> tuple[list[Assignment], int]:
        stmt = select(Assignment)
        if filters.student_id is not None:
            stmt = stmt.join(AssignmentStudent).where(
                AssignmentStudent.student_id == filters.student_id
            )
        if filters.status is not None:
            stmt = stmt.where(Assignment.status == filters.status)
        if filters.priority is not None:
            stmt = stmt.where(Assignment.priority == filters.priority)
        if filters.date_from is not None:
            stmt = stmt.where(Assignment.due_date >= filters.date_from)
        if filters.date_to is not None:
            stmt = stmt.where(Assignment.due_date <= filters.date_to)
        if filters.overdue_only:
            today = date.today()
            stmt = stmt.where(
                Assignment.due_date < today,
                Assignment.status.notin_(
                    [AssignmentStatus.DONE, AssignmentStatus.CANCELLED]
                ),
            )
        stmt = stmt.order_by(Assignment.due_date.asc())
        return self.paginate(stmt, offset=filters.offset, limit=filters.limit)
