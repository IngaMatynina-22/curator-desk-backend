from __future__ import annotations

from app.core.enums import AuditOperation
from app.models.academic_period import AcademicPeriod
from app.repositories.period_repository import PeriodRepository
from app.schemas.period import PeriodCreate, PeriodOut, PeriodUpdate
from app.services.audit_hooks import diff_fields
from app.services.base import BaseService
from app.services.parse import parse_schema


class PeriodService(BaseService):
    entity_type = "academic_period"

    def __init__(self, session):
        super().__init__(session)
        self.repo = PeriodRepository(session)

    def create(self, data: PeriodCreate | dict) -> PeriodOut:
        payload = parse_schema(PeriodCreate, data)
        if payload.is_current:
            self.repo.clear_current()
        period = AcademicPeriod(**payload.model_dump())
        self.repo.add(period)
        self.audit(period.id, AuditOperation.CREATE, payload.model_dump(mode="json"))
        self.commit()
        return PeriodOut.model_validate(period)

    def update(self, period_id: int, data: PeriodUpdate | dict) -> PeriodOut:
        payload = parse_schema(PeriodUpdate, data)
        period = self.repo.get_or_raise(period_id, "AcademicPeriod")
        values = payload.model_dump(exclude_unset=True)
        if values.get("is_current"):
            self.repo.clear_current()
        old = {k: getattr(period, k) for k in values}
        for key, value in values.items():
            setattr(period, key, value)
        self.flush()
        self.audit(period.id, AuditOperation.UPDATE, diff_fields(old, {**old, **values}))
        self.commit()
        return PeriodOut.model_validate(period)

    def set_current(self, period_id: int) -> PeriodOut:
        return self.update(period_id, {"is_current": True})

    def list(self, include_archived: bool = False) -> list[PeriodOut]:
        if include_archived:
            items = self.repo.list(include_archived=True, order_by=AcademicPeriod.starts_on.desc())
        else:
            items = self.repo.list_active()
        return [PeriodOut.model_validate(p) for p in items]

    def get(self, period_id: int) -> PeriodOut:
        return PeriodOut.model_validate(self.repo.get_or_raise(period_id, "AcademicPeriod"))

    def archive(self, period_id: int) -> PeriodOut:
        period = self.repo.get_or_raise(period_id, "AcademicPeriod")
        period.is_current = False
        self.repo.archive(period)
        self.audit(period.id, AuditOperation.ARCHIVE)
        self.commit()
        return PeriodOut.model_validate(period)

    def resolve_dates(self, period_id: int | None, date_from=None, date_to=None):
        if period_id is None:
            return date_from, date_to
        period = self.repo.get_or_raise(period_id, "AcademicPeriod")
        return date_from or period.starts_on, date_to or period.ends_on
