from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.core.enums import PeriodKind
from app.schemas.common import ORMModel


class PeriodCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    academic_year: str = Field(..., min_length=1, max_length=32)
    kind: PeriodKind = PeriodKind.SEMESTER
    starts_on: date
    ends_on: date
    is_current: bool = False

    @model_validator(mode="after")
    def validate_range(self) -> "PeriodCreate":
        if self.ends_on < self.starts_on:
            raise ValueError("ends_on cannot be before starts_on")
        return self


class PeriodUpdate(BaseModel):
    name: str | None = None
    academic_year: str | None = None
    kind: PeriodKind | None = None
    starts_on: date | None = None
    ends_on: date | None = None
    is_current: bool | None = None


class PeriodOut(ORMModel):
    id: int
    name: str
    academic_year: str
    kind: str
    starts_on: date
    ends_on: date
    is_current: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
