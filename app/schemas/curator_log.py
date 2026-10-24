from datetime import datetime

from pydantic import BaseModel, Field

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
