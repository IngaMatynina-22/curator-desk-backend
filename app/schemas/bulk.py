from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from app.core.enums import AttendanceStatus, AssignmentPriority, AssignmentStatus


class BulkResult(BaseModel):
    applied: int = 0
    skipped: int = 0
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    preview_only: bool = False
    details: list[dict[str, Any]] = Field(default_factory=list)


class GroupAttendanceRequest(BaseModel):
    lesson_id: int
    group_id: int
    default_status: AttendanceStatus = AttendanceStatus.PRESENT
    preview: bool = False


class BulkAssignmentUpdate(BaseModel):
    ids: list[int]
    status: AssignmentStatus | None = None
    priority: AssignmentPriority | None = None
    due_date: date | None = None
    preview: bool = False


class DutyPlanItem(BaseModel):
    duty_date: date
    student_ids: list[int] = Field(default_factory=list)
    start_time: str | None = None
    end_time: str | None = None
    location: str | None = None
    duty_type: str | None = None


class ScheduleDutiesRequest(BaseModel):
    plan: list[DutyPlanItem]
    preview: bool = False
