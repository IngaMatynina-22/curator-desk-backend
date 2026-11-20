from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.core.enums import AssignmentPriority, AssignmentStatus
from app.schemas.common import ORMModel


class AssignmentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    due_date: date
    priority: AssignmentPriority = AssignmentPriority.MEDIUM
    status: AssignmentStatus = AssignmentStatus.NEW
    author: str | None = None
    result_comment: str | None = None
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
    def normalize_description(cls, value: str | None) -> str | None:
        return value.strip() if value and value.strip() else None

    @field_validator("student_ids")
    @classmethod
    def unique_student_ids(cls, value: list[int]) -> list[int]:
        return list(dict.fromkeys(value))


class AssignmentUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    due_date: date | None = None
    priority: AssignmentPriority | None = None
    status: AssignmentStatus | None = None
    author: str | None = None
    result_comment: str | None = None
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
    def normalize_description(cls, value: str | None) -> str | None:
        return value.strip() if value and value.strip() else None

    @field_validator("student_ids")
    @classmethod
    def unique_student_ids(cls, value: list[int] | None) -> list[int] | None:
        return list(dict.fromkeys(value)) if value is not None else None


class AssignmentFilter(BaseModel):
    student_id: int | None = None
    status: AssignmentStatus | None = None
    priority: AssignmentPriority | None = None
    overdue_only: bool = False
    date_from: date | None = None
    date_to: date | None = None
    offset: int = 0
    limit: int = 50


class AssignmentOut(ORMModel):
    id: int
    title: str
    description: str | None
    due_date: date
    priority: str
    status: str
    effective_status: str | None = None
    is_overdue: bool = False
    author: str | None
    result_comment: str | None
    completed_at: datetime | None
    student_ids: list[int] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
