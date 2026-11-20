from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.enums import CuratorLogCategory
from app.schemas.common import ORMModel


class CuratorLogCreate(BaseModel):
    occurred_at: datetime
    category: CuratorLogCategory = CuratorLogCategory.OTHER
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    result: str | None = None
    next_actions: str | None = None
    event_id: int | None = None
    meeting_id: int | None = None
    student_ids: list[int] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title must not be empty")
        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Description must not be empty")
        return value

    @field_validator("student_ids")
    @classmethod
    def unique_student_ids(cls, value: list[int]) -> list[int]:
        return list(dict.fromkeys(value))


class CuratorLogUpdate(BaseModel):
    occurred_at: datetime | None = None
    category: CuratorLogCategory | None = None
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, min_length=1)
    result: str | None = None
    next_actions: str | None = None
    event_id: int | None = None
    meeting_id: int | None = None
    student_ids: list[int] | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Title must not be empty")
        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Description must not be empty")
        return value

    @field_validator("student_ids")
    @classmethod
    def unique_student_ids(cls, value: list[int] | None) -> list[int] | None:
        return list(dict.fromkeys(value)) if value is not None else None


class CuratorLogFilter(BaseModel):
    query: str | None = None
    category: CuratorLogCategory | None = None
    student_id: int | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    offset: int = 0
    limit: int = 50


class CuratorLogOut(ORMModel):
    id: int
    occurred_at: datetime
    category: str
    title: str
    description: str
    result: str | None
    next_actions: str | None
    event_id: int | None
    meeting_id: int | None
    student_ids: list[int] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
