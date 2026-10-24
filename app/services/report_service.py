from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from app.core.config import get_settings
from app.models.assignment import Assignment
from app.models.attendance import AttendanceRecord, Lesson
from app.models.curator_log import CuratorLog
from app.models.duty import Duty
from app.models.event import Event
from app.models.student import Student
from app.readers.import_export import export_csv, export_pdf, export_xlsx
from app.schemas.reports import ExportResult, ReportPeriod
from app.services.base import BaseService
from app.services.parse import parse_schema
from app.services.statistics_service import StatisticsService


class ReportService(BaseService):
    def __init__(self, session):
        super().__init__(session)
        self.stats = StatisticsService(session)

    def export_students(self, fmt: str = "csv", group_id: int | None = None) -> ExportResult:
        stmt = select(Student).where(Student.is_archived.is_(False)).order_by(Student.last_name)
        if group_id is not None:
            stmt = stmt.where(Student.group_id == group_id)
        students = list(self.session.scalars(stmt).all())
        headers = ["id", "student_number", "full_name", "status", "group_id", "email", "phone"]
        rows = [
            [s.id, s.student_number, s.full_name, s.status, s.group_id, s.email or "", s.phone or ""]
            for s in students
        ]
        return self._export("students", headers, rows, fmt)

    def export_attendance(self, period: ReportPeriod | dict | None = None, fmt: str = "csv") -> ExportResult:
        p = parse_schema(ReportPeriod, period or {})
        stmt = select(AttendanceRecord, Lesson).join(Lesson)
        if p.date_from:
            stmt = stmt.where(Lesson.lesson_date >= p.date_from)
        if p.date_to:
            stmt = stmt.where(Lesson.lesson_date <= p.date_to)
        rows_data = []
        for record, lesson in self.session.execute(stmt):
            rows_data.append(
                [
                    record.id,
                    record.student_id,
                    lesson.lesson_date.isoformat(),
                    lesson.subject_id,
                    record.status,
                    record.hours_missed,
                ]
            )
        headers = ["id", "student_id", "date", "subject_id", "status", "hours_missed"]
        return self._export("attendance", headers, rows_data, fmt)

    def export_assignments(self, fmt: str = "xlsx") -> ExportResult:
        items = list(self.session.scalars(select(Assignment).order_by(Assignment.due_date)).all())
        headers = ["id", "title", "due_date", "status", "priority", "effective_status"]
        rows = [
            [a.id, a.title, a.due_date.isoformat(), a.status, a.priority, a.effective_status]
            for a in items
        ]
        return self._export("assignments", headers, rows, fmt)

    def export_duties(self, fmt: str = "csv") -> ExportResult:
        items = list(self.session.scalars(select(Duty).order_by(Duty.duty_date)).all())
        headers = ["id", "date", "type", "status", "location", "students"]
        rows = [
            [
                d.id,
                d.duty_date.isoformat(),
                d.duty_type or "",
                d.status,
                d.location or "",
                ",".join(map(str, d.student_ids)),
            ]
            for d in items
        ]
        return self._export("duties", headers, rows, fmt)

    def export_events(self, fmt: str = "pdf") -> ExportResult:
        items = list(self.session.scalars(select(Event).order_by(Event.starts_at)).all())
        lines = [
            f"{e.starts_at:%Y-%m-%d %H:%M} | {e.title} | {e.status} | {e.location or '-'}"
            for e in items
        ]
        path = self._path("events", "pdf")
        count = export_pdf(path, "Events calendar", lines)
        return ExportResult(path=path, format="pdf", rows=count)

    def export_curator_log(self, fmt: str = "pdf") -> ExportResult:
        items = list(
            self.session.scalars(select(CuratorLog).order_by(CuratorLog.occurred_at.desc())).all()
        )
        lines = [
            f"{c.occurred_at:%Y-%m-%d} | {c.category} | {c.title}" for c in items
        ]
        path = self._path("curator_log", "pdf" if fmt == "pdf" else fmt)
        if fmt == "pdf":
            count = export_pdf(path, "Curator journal", lines)
        else:
            headers = ["id", "occurred_at", "category", "title"]
            rows = [[c.id, c.occurred_at.isoformat(), c.category, c.title] for c in items]
            count = self._write(path, headers, rows, fmt)
        return ExportResult(path=path, format=fmt, rows=count)

    def export_summary(self, period: ReportPeriod | dict | None = None, fmt: str = "pdf") -> ExportResult:
        stats = self.stats.overview(period)
        lines = [f"{key}: {value}" for key, value in stats.model_dump().items()]
        path = self._path("summary", fmt if fmt in {"pdf", "csv", "xlsx"} else "pdf")
        if path.suffix == ".pdf":
            count = export_pdf(path, "Semester/year summary", lines)
        else:
            headers = ["metric", "value"]
            rows = list(stats.model_dump().items())
            count = self._write(path, headers, rows, path.suffix.lstrip("."))
        return ExportResult(path=path, format=path.suffix.lstrip("."), rows=count)

    def _export(self, name: str, headers, rows, fmt: str) -> ExportResult:
        path = self._path(name, fmt)
        count = self._write(path, headers, rows, fmt)
        return ExportResult(path=path, format=fmt, rows=count)

    @staticmethod
    def _write(path: Path, headers, rows, fmt: str) -> int:
        if fmt == "csv":
            return export_csv(path, headers, rows)
        if fmt == "xlsx":
            return export_xlsx(path, headers, rows)
        if fmt == "pdf":
            lines = [", ".join(map(str, row)) for row in rows]
            return export_pdf(path, path.stem, lines)
        raise ValueError(f"unsupported export format: {fmt}")

    def _path(self, name: str, fmt: str) -> Path:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return get_settings().exports_dir / f"{name}_{stamp}.{fmt}"
