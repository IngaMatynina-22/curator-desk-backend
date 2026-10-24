from __future__ import annotations

from app.core.enums import AuditOperation
from app.core.exceptions import ConflictError
from app.models.associations import CuratorLogStudent
from app.models.curator_log import CuratorLog
from app.repositories.curator_log_repository import CuratorLogRepository
from app.repositories.student_repository import StudentRepository
from app.schemas.common import PageResult
from app.schemas.curator_log import CuratorLogCreate, CuratorLogFilter, CuratorLogOut, CuratorLogUpdate
from app.services.audit_hooks import diff_fields
from app.services.base import BaseService
from app.services.parse import parse_schema


class CuratorLogService(BaseService):
    entity_type = "curator_log"

    def __init__(self, session):
        super().__init__(session)
        self.repo = CuratorLogRepository(session)
        self.students = StudentRepository(session)

    def create(self, data: CuratorLogCreate | dict) -> CuratorLogOut:
        payload = parse_schema(CuratorLogCreate, data)
        self.students.ensure_ids_exist(payload.student_ids, "Student")
        if payload.meeting_id and self.repo.find_by_meeting(payload.meeting_id):
            raise ConflictError("curator log already exists for this meeting")
        if payload.event_id and self.repo.find_by_event(payload.event_id):
            raise ConflictError("curator log already exists for this event")
        entry = CuratorLog(**payload.model_dump(exclude={"student_ids"}))
        entry.student_links = [CuratorLogStudent(student_id=sid) for sid in payload.student_ids]
        self.repo.add(entry)
        self.audit(entry.id, AuditOperation.CREATE)
        self.commit()
        return self._to_out(entry)

    def update(self, log_id: int, data: CuratorLogUpdate | dict) -> CuratorLogOut:
        payload = parse_schema(CuratorLogUpdate, data)
        entry = self.repo.get_or_raise(log_id, "CuratorLog")
        values = payload.model_dump(exclude_unset=True)
        student_ids = values.pop("student_ids", None)
        old = {k: getattr(entry, k) for k in values}
        for key, value in values.items():
            setattr(entry, key, value)
        if student_ids is not None:
            self.students.ensure_ids_exist(student_ids, "Student")
            old["student_ids"] = entry.student_ids
            entry.student_links = [CuratorLogStudent(student_id=sid) for sid in student_ids]
            values["student_ids"] = student_ids
        self.flush()
        self.audit(entry.id, AuditOperation.UPDATE, diff_fields(old, {**old, **values}))
        self.commit()
        return self._to_out(entry)

    def get(self, log_id: int) -> CuratorLogOut:
        return self._to_out(self.repo.get_or_raise(log_id, "CuratorLog"))

    def list(self, filters: CuratorLogFilter | dict | None = None) -> PageResult[CuratorLogOut]:
        f = parse_schema(CuratorLogFilter, filters or {})
        items, total = self.repo.search(f)
        return PageResult(
            items=[self._to_out(e) for e in items],
            total=total,
            offset=f.offset,
            limit=f.limit,
        )

    def _to_out(self, entry: CuratorLog) -> CuratorLogOut:
        out = CuratorLogOut.model_validate(entry)
        out.student_ids = entry.student_ids
        return out
