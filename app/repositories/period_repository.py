from __future__ import annotations

from sqlalchemy import select, update

from app.models.academic_period import AcademicPeriod
from app.repositories.base import BaseRepository


class PeriodRepository(BaseRepository[AcademicPeriod]):
    model = AcademicPeriod

    def list_active(self) -> list[AcademicPeriod]:
        stmt = (
            select(AcademicPeriod)
            .where(AcademicPeriod.is_archived.is_(False))
            .order_by(AcademicPeriod.starts_on.desc())
        )
        return list(self.session.scalars(stmt).all())

    def clear_current(self) -> None:
        self.session.execute(update(AcademicPeriod).values(is_current=False))

    def get_current(self) -> AcademicPeriod | None:
        return self.session.scalar(
            select(AcademicPeriod).where(
                AcademicPeriod.is_current.is_(True),
                AcademicPeriod.is_archived.is_(False),
            )
        )
