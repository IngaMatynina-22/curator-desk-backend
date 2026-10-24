from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.core.enums import EventStatus, EventType
from app.schemas.common import ORMModel


class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    event_type: EventType = EventType.OTHER
    location: str | None = None
    starts_at: datetime
    ends_at: datetime
    status: EventStatus = EventStatus.PLANNED
    notes: str | None = None
    participant_ids: list[int] = Field(default_factory=list)
    responsible_ids: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_range(self) -> "EventCreate":
        if self.ends_at < self.starts_at:
            raise ValueError("ends_at cannot be before starts_at")
        return self


class EventUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    event_type: EventType | None = None
    location: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: EventStatus | None = None
    notes: str | None = None
    participant_ids: list[int] | None = None
    responsible_ids: list[int] | None = None


class EventFilter(BaseModel):
    query: str | None = None
    event_type: EventType | None = None
    status: EventStatus | None = None
    student_id: int | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    offset: int = 0
    limit: int = 50


class EventOut(ORMModel):
    id: int
    title: str
    description: str | None
    event_type: str
    location: str | None
    starts_at: datetime
    ends_at: datetime
    status: str
    notes: str | None
    participant_ids: list[int] = Field(default_factory=list)
    responsible_ids: list[int] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    warnings: list[str] = Field(default_factory=list)
