from __future__ import annotations

from sqlalchemy import or_, select

from app.models.note import Note
from app.repositories.base import BaseRepository


class NoteRepository(BaseRepository[Note]):
    model = Note

    def search(
        self,
        *,
        query: str | None = None,
        student_id: int | None = None,
        include_archived: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Note], int]:
        stmt = select(Note)
        if not include_archived:
            stmt = stmt.where(Note.is_archived.is_(False))
        if student_id is not None:
            stmt = stmt.where(Note.student_id == student_id)
        if query:
            q = f"%{query}%"
            stmt = stmt.where(or_(Note.title.ilike(q), Note.body.ilike(q)))
        stmt = stmt.order_by(Note.is_pinned.desc(), Note.updated_at.desc())
        return self.paginate(stmt, offset=offset, limit=limit)
