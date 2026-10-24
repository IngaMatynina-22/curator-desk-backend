from datetime import date, datetime

from pydantic import BaseModel, Field

from app.core.enums import TimelineKind
from app.schemas.common import ORMModel


class TimelineFilter(BaseModel):
    student_id: int
    date_from: date | datetime | None = None
    date_to: date | datetime | None = None
    period_id: int | None = None
    types: list[TimelineKind] | None = None
    offset: int = 0
    limit: int = Field(50, ge=1, le=500)


class TimelineItem(ORMModel):
    kind: str
    entity_id: int
    occurred_at: datetime
    title: str
    summary: str | None = None
    status: str | None = None
