from __future__ import annotations

from sqlalchemy import or_, select

from app.models.associations import EventStudent
from app.models.event import Event
from app.repositories.base import BaseRepository
from app.schemas.event import EventFilter


class EventRepository(BaseRepository[Event]):
    model = Event

    def search(self, filters: EventFilter) -> tuple[list[Event], int]:
        stmt = select(Event)
        if filters.student_id is not None:
            stmt = stmt.join(EventStudent).where(EventStudent.student_id == filters.student_id)
        if filters.query:
            q = f"%{filters.query}%"
            stmt = stmt.where(or_(Event.title.ilike(q), Event.description.ilike(q)))
        if filters.event_type is not None:
            stmt = stmt.where(Event.event_type == filters.event_type)
        if filters.status is not None:
            stmt = stmt.where(Event.status == filters.status)
        if filters.date_from is not None:
            stmt = stmt.where(Event.starts_at >= filters.date_from)
        if filters.date_to is not None:
            stmt = stmt.where(Event.starts_at <= filters.date_to)
        stmt = stmt.order_by(Event.starts_at.asc())
        return self.paginate(stmt, offset=filters.offset, limit=filters.limit)

    def find_overlaps(self, starts_at, ends_at, exclude_id: int | None = None) -> list[Event]:
        stmt = select(Event).where(Event.starts_at < ends_at, Event.ends_at > starts_at)
        if exclude_id is not None:
            stmt = stmt.where(Event.id != exclude_id)
        return list(self.session.scalars(stmt).all())
