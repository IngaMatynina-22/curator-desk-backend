from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.enums import AuditOperation, NoteCategory
from app.models.note import Note
from app.repositories.note_repository import NoteRepository
from app.schemas.common import ORMModel, PageResult
from app.services.audit_hooks import diff_fields
from app.services.base import BaseService
from app.services.parse import parse_schema


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    category: NoteCategory = NoteCategory.GENERAL
    is_pinned: bool = False
    student_id: int | None = None
    group_id: int | None = None
    event_id: int | None = None
    assignment_id: int | None = None


class NoteUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    category: NoteCategory | None = None
    is_pinned: bool | None = None
    student_id: int | None = None
    group_id: int | None = None
    event_id: int | None = None
    assignment_id: int | None = None


class NoteOut(ORMModel):
    id: int
    title: str
    body: str
    category: str
    is_pinned: bool
    student_id: int | None
    group_id: int | None
    event_id: int | None
    assignment_id: int | None
    is_archived: bool


class NoteService(BaseService):
    entity_type = "note"

    def __init__(self, session):
        super().__init__(session)
        self.repo = NoteRepository(session)

    def create(self, data: NoteCreate | dict) -> NoteOut:
        payload = parse_schema(NoteCreate, data)
        note = Note(**payload.model_dump())
        self.repo.add(note)
        self.audit(note.id, AuditOperation.CREATE)
        self.commit()
        return NoteOut.model_validate(note)

    def update(self, note_id: int, data: NoteUpdate | dict) -> NoteOut:
        payload = parse_schema(NoteUpdate, data)
        note = self.repo.get_or_raise(note_id, "Note")
        values = payload.model_dump(exclude_unset=True)
        old = {k: getattr(note, k) for k in values}
        for key, value in values.items():
            setattr(note, key, value)
        self.flush()
        self.audit(note.id, AuditOperation.UPDATE, diff_fields(old, {**old, **values}))
        self.commit()
        return NoteOut.model_validate(note)

    def pin(self, note_id: int, pinned: bool = True) -> NoteOut:
        return self.update(note_id, {"is_pinned": pinned})

    def archive(self, note_id: int) -> NoteOut:
        note = self.repo.get_or_raise(note_id, "Note")
        self.repo.archive(note)
        self.audit(note.id, AuditOperation.ARCHIVE)
        self.commit()
        return NoteOut.model_validate(note)

    def list(
        self,
        *,
        query: str | None = None,
        student_id: int | None = None,
        include_archived: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> PageResult[NoteOut]:
        items, total = self.repo.search(
            query=query,
            student_id=student_id,
            include_archived=include_archived,
            offset=offset,
            limit=limit,
        )
        return PageResult(
            items=[NoteOut.model_validate(n) for n in items],
            total=total,
            offset=offset,
            limit=limit,
        )
