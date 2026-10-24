from datetime import date, datetime

from pydantic import BaseModel, Field

from app.core.enums import MeetingFormat, MeetingStatus
from app.schemas.common import ORMModel


class MeetingCreate(BaseModel):
    scheduled_at: datetime
    format: MeetingFormat = MeetingFormat.INDIVIDUAL
    topic: str = Field(..., min_length=1, max_length=255)
    result_summary: str | None = None
    next_steps: str | None = None
    next_contact_date: date | None = None
    notes: str | None = None
    status: MeetingStatus = MeetingStatus.PLANNED
    student_ids: list[int] = Field(default_factory=list)


class MeetingUpdate(BaseModel):
    scheduled_at: datetime | None = None
    format: MeetingFormat | None = None
    topic: str | None = Field(None, min_length=1, max_length=255)
    result_summary: str | None = None
    next_steps: str | None = None
    next_contact_date: date | None = None
    notes: str | None = None
    status: MeetingStatus | None = None
    student_ids: list[int] | None = None


class MeetingFilter(BaseModel):
    student_id: int | None = None
    topic: str | None = None
    status: MeetingStatus | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    offset: int = 0
    limit: int = 50


class MeetingOut(ORMModel):
    id: int
    scheduled_at: datetime
    format: str
    topic: str
    result_summary: str | None
    next_steps: str | None
    next_contact_date: date | None
    notes: str | None
    status: str
    student_ids: list[int] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
