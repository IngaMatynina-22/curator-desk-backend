from datetime import date, datetime

from pydantic import BaseModel, Field

from app.core.enums import AttendanceStatus
from app.schemas.common import ORMModel


class LessonCreate(BaseModel):
    lesson_date: date
    subject_id: int
    pair_number: int | None = Field(None, ge=1, le=12)
    topic: str | None = None
    comment: str | None = None


class LessonOut(ORMModel):
    id: int
    lesson_date: date
    subject_id: int
    pair_number: int | None
    topic: str | None
    comment: str | None
    created_at: datetime
    updated_at: datetime


class AttendanceMark(BaseModel):
    student_id: int
    status: AttendanceStatus = AttendanceStatus.PRESENT
    hours_missed: float = Field(0, ge=0)
    reason: str | None = None
    comment: str | None = None


class AttendanceCreate(AttendanceMark):
    lesson_id: int


class AttendanceUpdate(BaseModel):
    status: AttendanceStatus | None = None
    hours_missed: float | None = Field(None, ge=0)
    reason: str | None = None
    comment: str | None = None


class BulkAttendanceCreate(BaseModel):
    lesson_id: int
    marks: list[AttendanceMark]


class AttendanceFilter(BaseModel):
    student_id: int | None = None
    subject_id: int | None = None
    status: AttendanceStatus | None = None
    date_from: date | None = None
    date_to: date | None = None
    offset: int = 0
    limit: int = 100


class AttendanceOut(ORMModel):
    id: int
    lesson_id: int
    student_id: int
    status: str
    hours_missed: float
    reason: str | None
    comment: str | None
    recorded_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AbsenceStats(BaseModel):
    student_id: int
    absences: int
    excused: int
    late: int
    hours_missed: float
