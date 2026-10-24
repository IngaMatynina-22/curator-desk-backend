from datetime import date
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ReportPeriod(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    group_id: int | None = None
    period_id: int | None = None


class StatisticsOut(BaseModel):
    students_total: int = 0
    students_active: int = 0
    students_archived: int = 0
    absences: int = 0
    excused_absences: int = 0
    events_planned: int = 0
    events_completed: int = 0
    assignments_done: int = 0
    assignments_overdue: int = 0
    duties_total: int = 0
    meetings_total: int = 0
    curator_logs_total: int = 0


class TrendPoint(BaseModel):
    bucket: str
    absences: int = 0
    excused: int = 0
    present: int = 0
    late: int = 0


class PeriodComparison(BaseModel):
    period_a: StatisticsOut
    period_b: StatisticsOut
    deltas: dict[str, int] = Field(default_factory=dict)


class OverdueSummary(BaseModel):
    overdue_count: int = 0
    top_titles: list[dict[str, Any]] = Field(default_factory=list)


class ActivitySummary(BaseModel):
    events_planned: int = 0
    events_completed: int = 0
    meetings_planned: int = 0
    meetings_completed: int = 0
    duties_planned: int = 0
    duties_done: int = 0
    curator_log_by_category: dict[str, int] = Field(default_factory=dict)


class ExportResult(BaseModel):
    path: Path
    format: str
    rows: int = 0
