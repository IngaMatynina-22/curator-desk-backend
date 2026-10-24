from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select

from app.core.enums import (
    AssignmentStatus,
    AttendanceStatus,
    DutyStatus,
    EventStatus,
    MeetingStatus,
    StudentStatus,
)
from app.models.assignment import Assignment
from app.models.attendance import AttendanceRecord, Lesson
from app.models.curator_log import CuratorLog
from app.models.duty import Duty
from app.models.event import Event
from app.models.meeting import Meeting
from app.models.student import Student
from app.schemas.reports import (
    ActivitySummary,
    OverdueSummary,
    PeriodComparison,
    ReportPeriod,
    StatisticsOut,
    TrendPoint,
)
from app.services.base import BaseService
from app.services.parse import parse_schema


class StatisticsService(BaseService):
    def overview(self, period: ReportPeriod | dict | None = None) -> StatisticsOut:
        p = self._resolve_period(period)
        student_filters = []
        if p.group_id is not None:
            student_filters.append(Student.group_id == p.group_id)

        students_total = self._count(Student, *student_filters)
        students_active = self._count(
            Student,
            Student.is_archived.is_(False),
            Student.status == StudentStatus.ACTIVE,
            *student_filters,
        )
        students_archived = self._count(Student, Student.is_archived.is_(True), *student_filters)

        absences = self._attendance_count(AttendanceStatus.ABSENT, p)
        excused = self._attendance_count(AttendanceStatus.EXCUSED, p)

        event_filters = self._dt_filters(Event.starts_at, p)
        events_planned = self._count(Event, Event.status == EventStatus.PLANNED, *event_filters)
        events_completed = self._count(
            Event, Event.status == EventStatus.COMPLETED, *event_filters
        )

        assign_filters = self._date_filters(Assignment.due_date, p)
        assignments_done = self._count(
            Assignment, Assignment.status == AssignmentStatus.DONE, *assign_filters
        )
        today = date.today()
        overdue_filters = [
            Assignment.due_date < today,
            Assignment.status.notin_([AssignmentStatus.DONE, AssignmentStatus.CANCELLED]),
            *assign_filters,
        ]
        assignments_overdue = self._count(Assignment, *overdue_filters)

        return StatisticsOut(
            students_total=students_total,
            students_active=students_active,
            students_archived=students_archived,
            absences=absences,
            excused_absences=excused,
            events_planned=events_planned,
            events_completed=events_completed,
            assignments_done=assignments_done,
            assignments_overdue=assignments_overdue,
            duties_total=self._count(Duty, *self._date_filters(Duty.duty_date, p)),
            meetings_total=self._count(Meeting, *self._dt_filters(Meeting.scheduled_at, p)),
            curator_logs_total=self._count(
                CuratorLog, *self._dt_filters(CuratorLog.occurred_at, p)
            ),
        )

    def get_attendance_trend(
        self,
        granularity: str = "week",
        date_from: date | None = None,
        date_to: date | None = None,
        group_id: int | None = None,
    ) -> list[TrendPoint]:
        date_to = date_to or date.today()
        date_from = date_from or (date_to - timedelta(days=84))
        stmt = (
            select(Lesson.lesson_date, AttendanceRecord.status, func.count())
            .join(AttendanceRecord, AttendanceRecord.lesson_id == Lesson.id)
            .where(Lesson.lesson_date >= date_from, Lesson.lesson_date <= date_to)
            .group_by(Lesson.lesson_date, AttendanceRecord.status)
        )
        if group_id is not None:
            stmt = stmt.join(Student, Student.id == AttendanceRecord.student_id).where(
                Student.group_id == group_id
            )
        buckets: dict[str, TrendPoint] = {}
        for lesson_date, status, count in self.session.execute(stmt):
            key = self._bucket(lesson_date, granularity)
            point = buckets.setdefault(key, TrendPoint(bucket=key))
            if status == AttendanceStatus.ABSENT:
                point.absences += int(count)
            elif status == AttendanceStatus.EXCUSED:
                point.excused += int(count)
            elif status == AttendanceStatus.PRESENT:
                point.present += int(count)
            elif status == AttendanceStatus.LATE:
                point.late += int(count)
        return [buckets[k] for k in sorted(buckets)]

    def compare_periods(
        self, period_a: ReportPeriod | dict, period_b: ReportPeriod | dict
    ) -> PeriodComparison:
        a = self.overview(period_a)
        b = self.overview(period_b)
        da, db = a.model_dump(), b.model_dump()
        deltas = {k: int(db[k]) - int(da[k]) for k in da if isinstance(da[k], int)}
        return PeriodComparison(period_a=a, period_b=b, deltas=deltas)

    def get_overdue_summary(self) -> OverdueSummary:
        today = date.today()
        rows = self.session.execute(
            select(Assignment.title, func.count())
            .where(
                Assignment.due_date < today,
                Assignment.status.notin_([AssignmentStatus.DONE, AssignmentStatus.CANCELLED]),
            )
            .group_by(Assignment.title)
            .order_by(func.count().desc())
            .limit(10)
        ).all()
        total = self._count(
            Assignment,
            Assignment.due_date < today,
            Assignment.status.notin_([AssignmentStatus.DONE, AssignmentStatus.CANCELLED]),
        )
        return OverdueSummary(
            overdue_count=total,
            top_titles=[{"title": t, "count": int(c)} for t, c in rows],
        )

    def get_activity_summary(self, period: ReportPeriod | dict | None = None) -> ActivitySummary:
        p = self._resolve_period(period)
        e_f = self._dt_filters(Event.starts_at, p)
        m_f = self._dt_filters(Meeting.scheduled_at, p)
        d_f = self._date_filters(Duty.duty_date, p)
        cat_rows = self.session.execute(
            select(CuratorLog.category, func.count())
            .where(*self._dt_filters(CuratorLog.occurred_at, p) or [True])
            .group_by(CuratorLog.category)
        ).all()
        return ActivitySummary(
            events_planned=self._count(Event, Event.status == EventStatus.PLANNED, *e_f),
            events_completed=self._count(Event, Event.status == EventStatus.COMPLETED, *e_f),
            meetings_planned=self._count(Meeting, Meeting.status == MeetingStatus.PLANNED, *m_f),
            meetings_completed=self._count(
                Meeting, Meeting.status == MeetingStatus.COMPLETED, *m_f
            ),
            duties_planned=self._count(Duty, Duty.status == DutyStatus.PLANNED, *d_f),
            duties_done=self._count(Duty, Duty.status == DutyStatus.DONE, *d_f),
            curator_log_by_category={str(c): int(n) for c, n in cat_rows},
        )

    def _resolve_period(self, period: ReportPeriod | dict | None) -> ReportPeriod:
        p = parse_schema(ReportPeriod, period or {})
        if p.period_id is not None:
            from app.models.academic_period import AcademicPeriod

            ap = self.session.get(AcademicPeriod, p.period_id)
            if ap:
                p.date_from = p.date_from or ap.starts_on
                p.date_to = p.date_to or ap.ends_on
        return p

    def _attendance_count(self, status: str, p: ReportPeriod) -> int:
        stmt = (
            select(func.count())
            .select_from(AttendanceRecord)
            .join(Lesson)
            .where(AttendanceRecord.status == status)
        )
        if p.date_from:
            stmt = stmt.where(Lesson.lesson_date >= p.date_from)
        if p.date_to:
            stmt = stmt.where(Lesson.lesson_date <= p.date_to)
        if p.group_id is not None:
            stmt = stmt.join(Student, Student.id == AttendanceRecord.student_id).where(
                Student.group_id == p.group_id
            )
        return int(self.session.scalar(stmt) or 0)

    @staticmethod
    def _date_filters(column, p: ReportPeriod) -> list:
        filters = []
        if p.date_from:
            filters.append(column >= p.date_from)
        if p.date_to:
            filters.append(column <= p.date_to)
        return filters

    @staticmethod
    def _dt_filters(column, p: ReportPeriod) -> list:
        filters = []
        if p.date_from:
            filters.append(column >= p.date_from)
        if p.date_to:
            filters.append(column <= p.date_to)
        return filters

    @staticmethod
    def _bucket(d: date, granularity: str) -> str:
        if granularity == "month":
            return f"{d.year:04d}-{d.month:02d}"
        iso = d.isocalendar()
        return f"{iso.year}-W{iso.week:02d}"

    def _count(self, model, *filters) -> int:
        stmt = select(func.count()).select_from(model)
        for f in filters:
            if f is True:
                continue
            stmt = stmt.where(f)
        return int(self.session.scalar(stmt) or 0)
