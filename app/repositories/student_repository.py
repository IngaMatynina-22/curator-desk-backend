from __future__ import annotations

from sqlalchemy import asc, desc, or_, select

from app.models.student import Student
from app.repositories.base import BaseRepository
from app.schemas.student import StudentFilter


class StudentRepository(BaseRepository[Student]):
    model = Student

    def search(self, filters: StudentFilter) -> tuple[list[Student], int]:
        stmt = select(Student)
        if not filters.include_archived:
            stmt = stmt.where(Student.is_archived.is_(False))
        if filters.group_id is not None:
            stmt = stmt.where(Student.group_id == filters.group_id)
        if filters.status is not None:
            stmt = stmt.where(Student.status == filters.status)
        if filters.query:
            q = f"%{filters.query.strip()}%"
            stmt = stmt.where(
                or_(
                    Student.last_name.ilike(q),
                    Student.first_name.ilike(q),
                    Student.middle_name.ilike(q),
                    Student.student_number.ilike(q),
                )
            )

        sort_map = {
            "last_name": Student.last_name,
            "first_name": Student.first_name,
            "student_number": Student.student_number,
            "status": Student.status,
            "created_at": Student.created_at,
        }
        col = sort_map.get(filters.sort_by, Student.last_name)
        stmt = stmt.order_by(desc(col) if filters.sort_dir == "desc" else asc(col))
        return self.paginate(stmt, offset=filters.offset, limit=filters.limit)

    def get_by_number(self, student_number: str) -> Student | None:
        return self.session.scalar(
            select(Student).where(Student.student_number == student_number)
        )
