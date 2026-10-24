"""Shared Pydantic schemas."""

from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PageParams(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=500)


class PageResult(BaseModel, Generic[T]):
    items: list[T]
    total: int
    offset: int
    limit: int


class DateRangeFilter(BaseModel):
    date_from: date | datetime | None = None
    date_to: date | datetime | None = None


class MessageOut(BaseModel):
    message: str
    warnings: list[str] = Field(default_factory=list)
