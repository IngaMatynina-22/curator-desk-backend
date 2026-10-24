from __future__ import annotations

from pydantic import ValidationError as PydanticValidationError

from app.core.enums import AuditOperation
from app.core.exceptions import ValidationError
from app.models.academic_group import AcademicGroup
from app.repositories.group_repository import GroupRepository
from app.schemas.common import PageResult
from app.schemas.group import GroupCreate, GroupFilter, GroupOut, GroupUpdate
from app.services.audit_hooks import diff_fields
from app.services.base import BaseService


class GroupService(BaseService):
    entity_type = "academic_group"

    def __init__(self, session):
        super().__init__(session)
        self.repo = GroupRepository(session)

    def create(self, data: GroupCreate | dict) -> GroupOut:
        payload = self._parse(GroupCreate, data)
        group = AcademicGroup(**payload.model_dump())
        self.repo.add(group)
        self.audit(group.id, AuditOperation.CREATE, payload.model_dump())
        self.commit()
        return self._to_out(group)

    def update(self, group_id: int, data: GroupUpdate | dict) -> GroupOut:
        payload = self._parse(GroupUpdate, data)
        group = self.repo.get_or_raise(group_id, "Group")
        old = {
            "name": group.name,
            "specialty": group.specialty,
            "course": group.course,
            "academic_year": group.academic_year,
            "curator_name": group.curator_name,
        }
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(group, key, value)
        self.flush()
        changes = diff_fields(old, {**old, **payload.model_dump(exclude_unset=True)})
        self.audit(group.id, AuditOperation.UPDATE, changes)
        self.commit()
        return self._to_out(group)

    def get(self, group_id: int) -> GroupOut:
        return self._to_out(self.repo.get_or_raise(group_id, "Group"))

    def list(self, filters: GroupFilter | dict | None = None) -> PageResult[GroupOut]:
        f = self._parse(GroupFilter, filters or {})
        items, total = self.repo.search(f)
        return PageResult(
            items=[self._to_out(g) for g in items],
            total=total,
            offset=f.offset,
            limit=f.limit,
        )

    def archive(self, group_id: int) -> GroupOut:
        group = self.repo.get_or_raise(group_id, "Group")
        self.repo.archive(group)
        self.audit(group.id, AuditOperation.ARCHIVE)
        self.commit()
        return self._to_out(group)

    def restore(self, group_id: int) -> GroupOut:
        group = self.repo.get_or_raise(group_id, "Group")
        self.repo.restore(group)
        self.audit(group.id, AuditOperation.RESTORE)
        self.commit()
        return self._to_out(group)

    def count(self, include_archived: bool = False) -> int:
        return self.repo.count(include_archived=include_archived)

    def _to_out(self, group: AcademicGroup) -> GroupOut:
        out = GroupOut.model_validate(group)
        out.active_students = self.repo.count_active_students(group.id)
        return out

    @staticmethod
    def _parse(model, data):
        try:
            if isinstance(data, model):
                return data
            return model.model_validate(data)
        except PydanticValidationError as exc:
            raise ValidationError(str(exc)) from exc
