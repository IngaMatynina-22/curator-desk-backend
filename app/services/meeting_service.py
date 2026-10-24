from __future__ import annotations

from app.core.enums import AuditOperation, MeetingStatus
from app.models.associations import MeetingStudent
from app.models.meeting import Meeting
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.student_repository import StudentRepository
from app.schemas.common import PageResult
from app.schemas.meeting import MeetingCreate, MeetingFilter, MeetingOut, MeetingUpdate
from app.services.audit_hooks import diff_fields
from app.services.base import BaseService
from app.services.parse import parse_schema


class MeetingService(BaseService):
    entity_type = "meeting"

    def __init__(self, session):
        super().__init__(session)
        self.repo = MeetingRepository(session)
        self.students = StudentRepository(session)

    def create(self, data: MeetingCreate | dict) -> MeetingOut:
        payload = parse_schema(MeetingCreate, data)
        self.students.ensure_ids_exist(payload.student_ids, "Student")
        meeting = Meeting(**payload.model_dump(exclude={"student_ids"}))
        meeting.student_links = [MeetingStudent(student_id=sid) for sid in payload.student_ids]
        self.repo.add(meeting)
        self.audit(meeting.id, AuditOperation.CREATE)
        self.commit()
        return self._to_out(meeting)

    def update(self, meeting_id: int, data: MeetingUpdate | dict) -> MeetingOut:
        payload = parse_schema(MeetingUpdate, data)
        meeting = self.repo.get_or_raise(meeting_id, "Meeting")
        values = payload.model_dump(exclude_unset=True)
        student_ids = values.pop("student_ids", None)
        old = {k: getattr(meeting, k) for k in values}
        for key, value in values.items():
            setattr(meeting, key, value)
        if student_ids is not None:
            self.students.ensure_ids_exist(student_ids, "Student")
            old["student_ids"] = meeting.student_ids
            meeting.student_links = [MeetingStudent(student_id=sid) for sid in student_ids]
            values["student_ids"] = student_ids
        self.flush()
        self.audit(meeting.id, AuditOperation.UPDATE, diff_fields(old, {**old, **values}))
        self.commit()
        return self._to_out(meeting)

    def complete(self, meeting_id: int, result_summary: str | None = None) -> MeetingOut:
        return self.update(
            meeting_id,
            {"status": MeetingStatus.COMPLETED, "result_summary": result_summary},
        )

    def cancel(self, meeting_id: int) -> MeetingOut:
        return self.update(meeting_id, {"status": MeetingStatus.CANCELLED})

    def get(self, meeting_id: int) -> MeetingOut:
        return self._to_out(self.repo.get_or_raise(meeting_id, "Meeting"))

    def list(self, filters: MeetingFilter | dict | None = None) -> PageResult[MeetingOut]:
        f = parse_schema(MeetingFilter, filters or {})
        items, total = self.repo.search(f)
        return PageResult(
            items=[self._to_out(m) for m in items],
            total=total,
            offset=f.offset,
            limit=f.limit,
        )

    def _to_out(self, meeting: Meeting) -> MeetingOut:
        out = MeetingOut.model_validate(meeting)
        out.student_ids = meeting.student_ids
        return out
