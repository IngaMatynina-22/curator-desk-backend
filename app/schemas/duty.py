from datetime import date, datetime, time

from pydantic import BaseModel, Field, model_validator

from app.core.enums import DutyStatus
from app.schemas.common import ORMModel


class DutyCreate(BaseModel):
    duty_date: date
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = None
    duty_type: str | None = None
    status: DutyStatus = DutyStatus.PLANNED
    comment: str | None = None
    student_ids: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_times(self) -> "DutyCreate":
        if self.start_time and self.end_time and self.end_time < self.start_time:
            raise ValueError("end_time cannot be before start_time")
        return self


class DutyUpdate(BaseModel):
    duty_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = None
    duty_type: str | None = None
    status: DutyStatus | None = None
    comment: str | None = None
    student_ids: list[int] | None = None


class DutyFilter(BaseModel):
    student_id: int | None = None
    status: DutyStatus | None = None
    date_from: date | None = None
    date_to: date | None = None
    offset: int = 0
    limit: int = 50


class DutyOut(ORMModel):
    id: int
    duty_date: date
    start_time: time | None
    end_time: time | None
    location: str | None
    duty_type: str | None
    status: str
    comment: str | None
    student_ids: list[int] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    warnings: list[str] = Field(default_factory=list)
