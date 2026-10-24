from __future__ import annotations

from sqlalchemy import or_, select

from app.models.associations import MeetingStudent
from app.models.meeting import Meeting
from app.repositories.base import BaseRepository
from app.schemas.meeting import MeetingFilter


class MeetingRepository(BaseRepository[Meeting]):
    model = Meeting

    def search(self, filters: MeetingFilter) -> tuple[list[Meeting], int]:
        stmt = select(Meeting)
        if filters.student_id is not None:
            stmt = stmt.join(MeetingStudent).where(
                MeetingStudent.student_id == filters.student_id
            )
        if filters.topic:
            stmt = stmt.where(Meeting.topic.ilike(f"%{filters.topic}%"))
        if filters.status is not None:
            stmt = stmt.where(Meeting.status == filters.status)
        if filters.date_from is not None:
            stmt = stmt.where(Meeting.scheduled_at >= filters.date_from)
        if filters.date_to is not None:
            stmt = stmt.where(Meeting.scheduled_at <= filters.date_to)
        stmt = stmt.order_by(Meeting.scheduled_at.desc())
        return self.paginate(stmt, offset=filters.offset, limit=filters.limit)
