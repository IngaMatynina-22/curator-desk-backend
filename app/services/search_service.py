from __future__ import annotations

from sqlalchemy import or_, select

from app.models.curator_log import CuratorLog
from app.models.event import Event
from app.models.note import Note
from app.models.student import Student
from app.schemas.search import GlobalSearchQuery, GlobalSearchResult, SearchHit
from app.services.base import BaseService
from app.services.parse import parse_schema


class SearchService(BaseService):
    def search(self, data: GlobalSearchQuery | dict) -> GlobalSearchResult:
        q = parse_schema(GlobalSearchQuery, data)
        pattern = f"%{q.query.strip()}%"
        students = self.session.scalars(
            select(Student)
            .where(
                Student.is_archived.is_(False),
                or_(
                    Student.last_name.ilike(pattern),
                    Student.first_name.ilike(pattern),
                    Student.student_number.ilike(pattern),
                ),
            )
            .offset(q.offset)
            .limit(q.limit)
        ).all()
        events = self.session.scalars(
            select(Event)
            .where(or_(Event.title.ilike(pattern), Event.description.ilike(pattern)))
            .offset(q.offset)
            .limit(q.limit)
        ).all()
        notes = self.session.scalars(
            select(Note)
            .where(
                Note.is_archived.is_(False),
                or_(Note.title.ilike(pattern), Note.body.ilike(pattern)),
            )
            .offset(q.offset)
            .limit(q.limit)
        ).all()
        logs = self.session.scalars(
            select(CuratorLog)
            .where(
                or_(CuratorLog.title.ilike(pattern), CuratorLog.description.ilike(pattern))
            )
            .offset(q.offset)
            .limit(q.limit)
        ).all()
        return GlobalSearchResult(
            students=[
                SearchHit(entity_type="student", entity_id=s.id, title=s.full_name)
                for s in students
            ],
            events=[
                SearchHit(entity_type="event", entity_id=e.id, title=e.title) for e in events
            ],
            notes=[
                SearchHit(entity_type="note", entity_id=n.id, title=n.title, snippet=n.body[:120])
                for n in notes
            ],
            curator_logs=[
                SearchHit(entity_type="curator_log", entity_id=c.id, title=c.title)
                for c in logs
            ],
        )
