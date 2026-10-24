from __future__ import annotations

from app.core.date_utils import utc_now
from app.core.enums import AssignmentStatus, AuditOperation
from app.models.assignment import Assignment
from app.models.associations import AssignmentStudent
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.student_repository import StudentRepository
from app.schemas.assignment import AssignmentCreate, AssignmentFilter, AssignmentOut, AssignmentUpdate
from app.schemas.common import PageResult
from app.services.audit_hooks import diff_fields
from app.services.base import BaseService
from app.services.parse import parse_schema


class AssignmentService(BaseService):
    entity_type = "assignment"

    def __init__(self, session):
        super().__init__(session)
        self.repo = AssignmentRepository(session)
        self.students = StudentRepository(session)

    def create(self, data: AssignmentCreate | dict) -> AssignmentOut:
        payload = parse_schema(AssignmentCreate, data)
        self.students.ensure_ids_exist(payload.student_ids, "Student")
        entity = Assignment(**payload.model_dump(exclude={"student_ids"}))
        entity.student_links = [AssignmentStudent(student_id=sid) for sid in payload.student_ids]
        self.repo.add(entity)
        self.audit(entity.id, AuditOperation.CREATE)
        self.commit()
        return self._to_out(entity)

    def update(self, assignment_id: int, data: AssignmentUpdate | dict) -> AssignmentOut:
        payload = parse_schema(AssignmentUpdate, data)
        entity = self.repo.get_or_raise(assignment_id, "Assignment")
        values = payload.model_dump(exclude_unset=True)
        student_ids = values.pop("student_ids", None)
        if "status" in values and values["status"] == AssignmentStatus.DONE:
            values.setdefault("completed_at", utc_now())
        old = {k: getattr(entity, k) for k in values}
        for key, value in values.items():
            setattr(entity, key, value)
        if student_ids is not None:
            self.students.ensure_ids_exist(student_ids, "Student")
            old["student_ids"] = entity.student_ids
            entity.student_links = [AssignmentStudent(student_id=sid) for sid in student_ids]
            values["student_ids"] = student_ids
        self.flush()
        self.audit(entity.id, AuditOperation.UPDATE, diff_fields(old, {**old, **values}))
        self.commit()
        return self._to_out(entity)

    def complete(self, assignment_id: int, result_comment: str | None = None) -> AssignmentOut:
        return self.update(
            assignment_id,
            {
                "status": AssignmentStatus.DONE,
                "result_comment": result_comment,
                "completed_at": utc_now(),
            },
        )

    def get(self, assignment_id: int) -> AssignmentOut:
        return self._to_out(self.repo.get_or_raise(assignment_id, "Assignment"))

    def list(self, filters: AssignmentFilter | dict | None = None) -> PageResult[AssignmentOut]:
        f = parse_schema(AssignmentFilter, filters or {})
        items, total = self.repo.search(f)
        return PageResult(
            items=[self._to_out(a) for a in items],
            total=total,
            offset=f.offset,
            limit=f.limit,
        )

    def overdue(self) -> list[AssignmentOut]:
        result = self.list(AssignmentFilter(overdue_only=True, limit=500))
        return result.items

    def _to_out(self, entity: Assignment) -> AssignmentOut:
        out = AssignmentOut.model_validate(entity)
        out.student_ids = entity.student_ids
        out.is_overdue = entity.is_overdue
        out.effective_status = entity.effective_status
        return out
