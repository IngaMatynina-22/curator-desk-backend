from typing import Any

from pydantic import BaseModel, Field


class ImportMapping(BaseModel):
    student_number: str = "student_number"
    last_name: str = "last_name"
    first_name: str = "first_name"
    middle_name: str | None = "middle_name"
    email: str | None = "email"
    phone: str | None = "phone"


class ImportRowResult(BaseModel):
    row_index: int
    action: str  # create | skip | error | warning
    student_number: str | None = None
    message: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class ImportReport(BaseModel):
    job_id: int | None = None
    valid: bool = False
    total_rows: int = 0
    to_create: int = 0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    rows: list[ImportRowResult] = Field(default_factory=list)
