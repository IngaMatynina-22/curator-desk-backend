from __future__ import annotations

from sqlalchemy import or_, select

from app.models.associations import CuratorLogStudent
from app.models.curator_log import CuratorLog
from app.repositories.base import BaseRepository
from app.schemas.curator_log import CuratorLogFilter


class CuratorLogRepository(BaseRepository[CuratorLog]):
    model = CuratorLog

    def search(self, filters: CuratorLogFilter) -> tuple[list[CuratorLog], int]:
        stmt = select(CuratorLog)
        if filters.student_id is not None:
            stmt = stmt.join(CuratorLogStudent).where(
                CuratorLogStudent.student_id == filters.student_id
            )
        if filters.category is not None:
            stmt = stmt.where(CuratorLog.category == filters.category)
        if filters.query:
            q = f"%{filters.query}%"
            stmt = stmt.where(
                or_(CuratorLog.title.ilike(q), CuratorLog.description.ilike(q))
            )
        if filters.date_from is not None:
            stmt = stmt.where(CuratorLog.occurred_at >= filters.date_from)
        if filters.date_to is not None:
            stmt = stmt.where(CuratorLog.occurred_at <= filters.date_to)
        stmt = stmt.order_by(CuratorLog.occurred_at.desc())
        return self.paginate(stmt, offset=filters.offset, limit=filters.limit)

    def find_by_meeting(self, meeting_id: int) -> CuratorLog | None:
        return self.session.scalar(
            select(CuratorLog).where(CuratorLog.meeting_id == meeting_id)
        )

    def find_by_event(self, event_id: int) -> CuratorLog | None:
        return self.session.scalar(select(CuratorLog).where(CuratorLog.event_id == event_id))
