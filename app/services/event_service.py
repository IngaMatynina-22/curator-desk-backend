from __future__ import annotations

from app.core.enums import AuditOperation, EventStatus, EventStudentRole
from app.core.exceptions import ValidationError
from app.models.associations import EventStudent
from app.models.event import Event
from app.repositories.event_repository import EventRepository
from app.repositories.student_repository import StudentRepository
from app.schemas.common import PageResult
from app.schemas.event import EventCreate, EventFilter, EventOut, EventUpdate
from app.services.audit_hooks import diff_fields
from app.services.base import BaseService
from app.services.parse import parse_schema


class EventService(BaseService):
    entity_type = "event"

    def __init__(self, session):
        super().__init__(session)
        self.repo = EventRepository(session)
        self.students = StudentRepository(session)

    def create(self, data: EventCreate | dict) -> EventOut:
        payload = parse_schema(EventCreate, data)
        all_ids = list(set(payload.participant_ids + payload.responsible_ids))
        self.students.ensure_ids_exist(all_ids, "Student")
        warnings = self._overlap_warnings(payload.starts_at, payload.ends_at)
        event = Event(**payload.model_dump(exclude={"participant_ids", "responsible_ids"}))
        event.student_links = self._links(payload.participant_ids, payload.responsible_ids)
        self.repo.add(event)
        self.audit(event.id, AuditOperation.CREATE)
        self.commit()
        return self._to_out(event, warnings)

    def update(self, event_id: int, data: EventUpdate | dict) -> EventOut:
        payload = parse_schema(EventUpdate, data)
        event = self.repo.get_or_raise(event_id, "Event")
        values = payload.model_dump(exclude_unset=True)
        participants = values.pop("participant_ids", None)
        responsible = values.pop("responsible_ids", None)
        if "status" in values:
            self._validate_status_transition(event.status, values["status"])
        old = {k: getattr(event, k) for k in values}
        for key, value in values.items():
            setattr(event, key, value)
        if event.ends_at < event.starts_at:
            raise ValidationError("ends_at cannot be before starts_at")
        if participants is not None or responsible is not None:
            p = participants if participants is not None else event.participant_ids
            r = responsible if responsible is not None else event.responsible_ids
            self.students.ensure_ids_exist(list(set(p + r)), "Student")
            old["participant_ids"] = event.participant_ids
            old["responsible_ids"] = event.responsible_ids
            event.student_links = self._links(p, r)
            values["participant_ids"] = p
            values["responsible_ids"] = r
        warnings = self._overlap_warnings(event.starts_at, event.ends_at, exclude_id=event.id)
        self.flush()
        self.audit(event.id, AuditOperation.UPDATE, diff_fields(old, {**old, **values}))
        self.commit()
        return self._to_out(event, warnings)

    def cancel(self, event_id: int) -> EventOut:
        return self.update(event_id, {"status": EventStatus.CANCELLED})

    def get(self, event_id: int) -> EventOut:
        return self._to_out(self.repo.get_or_raise(event_id, "Event"))

    def list(self, filters: EventFilter | dict | None = None) -> PageResult[EventOut]:
        f = parse_schema(EventFilter, filters or {})
        items, total = self.repo.search(f)
        return PageResult(
            items=[self._to_out(e) for e in items],
            total=total,
            offset=f.offset,
            limit=f.limit,
        )

    def _overlap_warnings(self, starts_at, ends_at, exclude_id=None) -> list[str]:
        overlaps = self.repo.find_overlaps(starts_at, ends_at, exclude_id)
        return [f"overlapping event id={e.id}: {e.title}" for e in overlaps]

    @staticmethod
    def _validate_status_transition(old: str, new: str) -> None:
        if old == EventStatus.CANCELLED and new == EventStatus.COMPLETED:
            raise ValidationError("cannot mark cancelled event as completed without reopening")

    @staticmethod
    def _links(participants: list[int], responsible: list[int]) -> list[EventStudent]:
        links = [
            EventStudent(student_id=sid, role=EventStudentRole.PARTICIPANT)
            for sid in participants
        ]
        links.extend(
            EventStudent(student_id=sid, role=EventStudentRole.RESPONSIBLE)
            for sid in responsible
        )
        return links

    def _to_out(self, event: Event, warnings: list[str] | None = None) -> EventOut:
        out = EventOut.model_validate(event)
        out.participant_ids = event.participant_ids
        out.responsible_ids = event.responsible_ids
        out.warnings = warnings or []
        return out
