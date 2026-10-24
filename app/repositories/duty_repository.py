from __future__ import annotations

from sqlalchemy import and_, or_, select

from app.models.associations import DutyStudent
from app.models.duty import Duty
from app.repositories.base import BaseRepository
from app.schemas.duty import DutyFilter


class DutyRepository(BaseRepository[Duty]):
    model = Duty

    def search(self, filters: DutyFilter) -> tuple[list[Duty], int]:
        stmt = select(Duty)
        if filters.student_id is not None:
            stmt = stmt.join(DutyStudent).where(DutyStudent.student_id == filters.student_id)
        if filters.status is not None:
            stmt = stmt.where(Duty.status == filters.status)
        if filters.date_from is not None:
            stmt = stmt.where(Duty.duty_date >= filters.date_from)
        if filters.date_to is not None:
            stmt = stmt.where(Duty.duty_date <= filters.date_to)
        stmt = stmt.order_by(Duty.duty_date.desc())
        return self.paginate(stmt, offset=filters.offset, limit=filters.limit)

    def find_overlaps(
        self,
        student_ids: list[int],
        duty_date,
        start_time,
        end_time,
        exclude_id: int | None = None,
    ) -> list[Duty]:
        if not student_ids:
            return []
        stmt = (
            select(Duty)
            .join(DutyStudent)
            .where(
                DutyStudent.student_id.in_(student_ids),
                Duty.duty_date == duty_date,
            )
        )
        if exclude_id is not None:
            stmt = stmt.where(Duty.id != exclude_id)
        duties = list(self.session.scalars(stmt).unique().all())
        if start_time is None or end_time is None:
            return duties
        overlaps = []
        for duty in duties:
            if duty.start_time is None or duty.end_time is None:
                overlaps.append(duty)
                continue
            if start_time < duty.end_time and end_time > duty.start_time:
                overlaps.append(duty)
        return overlaps
