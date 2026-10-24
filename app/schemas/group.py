from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    specialty: str = Field(..., min_length=1, max_length=255)
    course: int = Field(..., ge=1, le=10)
    academic_year: str = Field(..., min_length=1, max_length=32)
    curator_name: str | None = None


class GroupUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=64)
    specialty: str | None = Field(None, min_length=1, max_length=255)
    course: int | None = Field(None, ge=1, le=10)
    academic_year: str | None = Field(None, min_length=1, max_length=32)
    curator_name: str | None = None


class GroupFilter(BaseModel):
    query: str | None = None
    academic_year: str | None = None
    course: int | None = None
    include_archived: bool = False
    offset: int = 0
    limit: int = 50


class GroupOut(ORMModel):
    id: int
    name: str
    specialty: str
    course: int
    academic_year: str
    curator_name: str | None
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    active_students: int | None = None
