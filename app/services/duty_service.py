from __future__ import annotations

from app.core.enums import AuditOperation
from app.models.associations import DutyStudent
from app.models.duty import Duty
from app.repositories.duty_repository import DutyRepository
from app.repositories.student_repository import StudentRepository
from app.schemas.common import PageResult
from app.schemas.duty import DutyCreate, DutyFilter, DutyOut, DutyUpdate
from app.services.audit_hooks import diff_fields
from app.services.base import BaseService
from app.services.parse import parse_schema


class DutyService(BaseService):
    entity_type = "duty"

    def __init__(self, session):
        super().__init__(session)
        self.repo = DutyRepository(session)
        self.students = StudentRepository(session)

    def create(self, data: DutyCreate | dict) -> DutyOut:
        payload = parse_schema(DutyCreate, data)
        self.students.ensure_ids_exist(payload.student_ids, "Student")
        warnings = self._overlap_warnings(
            payload.student_ids, payload.duty_date, payload.start_time, payload.end_time
        )
        duty = Duty(**payload.model_dump(exclude={"student_ids"}))
        duty.student_links = [DutyStudent(student_id=sid) for sid in payload.student_ids]
        self.repo.add(duty)
        self.audit(duty.id, AuditOperation.CREATE)
        self.commit()
        return self._to_out(duty, warnings)

    def update(self, duty_id: int, data: DutyUpdate | dict) -> DutyOut:
        payload = parse_schema(DutyUpdate, data)
        duty = self.repo.get_or_raise(duty_id, "Duty")
        values = payload.model_dump(exclude_unset=True)
        student_ids = values.pop("student_ids", None)
        old = {k: getattr(duty, k) for k in values}
        for key, value in values.items():
            setattr(duty, key, value)
        if student_ids is not None:
            self.students.ensure_ids_exist(student_ids, "Student")
            old["student_ids"] = duty.student_ids
            duty.student_links = [DutyStudent(student_id=sid) for sid in student_ids]
            values["student_ids"] = student_ids
        warnings = self._overlap_warnings(
            duty.student_ids, duty.duty_date, duty.start_time, duty.end_time, exclude_id=duty.id
        )
        self.flush()
        self.audit(duty.id, AuditOperation.UPDATE, diff_fields(old, {**old, **values}))
        self.commit()
        return self._to_out(duty, warnings)

    def get(self, duty_id: int) -> DutyOut:
        return self._to_out(self.repo.get_or_raise(duty_id, "Duty"))

    def list(self, filters: DutyFilter | dict | None = None) -> PageResult[DutyOut]:
        f = parse_schema(DutyFilter, filters or {})
        items, total = self.repo.search(f)
        return PageResult(
            items=[self._to_out(d) for d in items],
            total=total,
            offset=f.offset,
            limit=f.limit,
        )

    def _overlap_warnings(self, student_ids, duty_date, start, end, exclude_id=None) -> list[str]:
        overlaps = self.repo.find_overlaps(student_ids, duty_date, start, end, exclude_id)
        if not overlaps:
            return []
        return [f"overlapping duty id={d.id} on {d.duty_date}" for d in overlaps]

    def _to_out(self, duty: Duty, warnings: list[str] | None = None) -> DutyOut:
        out = DutyOut.model_validate(duty)
        out.student_ids = duty.student_ids
        out.warnings = warnings or []
        return out
