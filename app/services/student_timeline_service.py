from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import select

from app.core.enums import TimelineKind
from app.models.academic_record import AcademicRecord
from app.models.assignment import Assignment
from app.models.associations import (
    AssignmentStudent,
    CuratorLogStudent,
    DutyStudent,
    EventStudent,
    MeetingStudent,
)
from app.models.attendance import AttendanceRecord, Lesson
from app.models.curator_log import CuratorLog
from app.models.duty import Duty
from app.models.event import Event
from app.models.meeting import Meeting
from app.models.note import Note
from app.repositories.student_repository import StudentRepository
from app.schemas.common import PageResult
from app.schemas.timeline import TimelineFilter, TimelineItem
from app.services.base import BaseService
from app.services.parse import parse_schema


class StudentTimelineService(BaseService):
    def __init__(self, session):
        super().__init__(session)
        self.students = StudentRepository(session)

    def get_timeline(
        self,
        student_id: int | TimelineFilter | dict,
        date_from=None,
        date_to=None,
        types=None,
        limit: int = 50,
        offset: int = 0,
        period_id: int | None = None,
    ) -> PageResult[TimelineItem]:
        if isinstance(student_id, (TimelineFilter, dict)):
            f = parse_schema(TimelineFilter, student_id)
        else:
            f = TimelineFilter(
                student_id=student_id,
                date_from=date_from,
                date_to=date_to,
                types=types,
                limit=limit,
                offset=offset,
                period_id=period_id,
            )
        self.students.get_or_raise(f.student_id, "Student")
        date_from, date_to = self._resolve_dates(f)
        kinds = set(f.types) if f.types else set(TimelineKind)
        items: list[TimelineItem] = []

        if TimelineKind.ATTENDANCE in kinds:
            items.extend(self._attendance(f.student_id, date_from, date_to))
        if TimelineKind.ACADEMIC in kinds:
            items.extend(self._academic(f.student_id, date_from, date_to))
        if TimelineKind.ASSIGNMENT in kinds:
            items.extend(self._assignments(f.student_id, date_from, date_to))
        if TimelineKind.DUTY in kinds:
            items.extend(self._duties(f.student_id, date_from, date_to))
        if TimelineKind.EVENT in kinds:
            items.extend(self._events(f.student_id, date_from, date_to))
        if TimelineKind.MEETING in kinds:
            items.extend(self._meetings(f.student_id, date_from, date_to))
        if TimelineKind.CURATOR_LOG in kinds:
            items.extend(self._logs(f.student_id, date_from, date_to))
        if TimelineKind.NOTE in kinds:
            items.extend(self._notes(f.student_id, date_from, date_to))

        items.sort(key=lambda x: x.occurred_at, reverse=True)
        total = len(items)
        page = items[f.offset : f.offset + f.limit]
        return PageResult(items=page, total=total, offset=f.offset, limit=f.limit)

    def _resolve_dates(self, f: TimelineFilter) -> tuple[datetime | None, datetime | None]:
        date_from = f.date_from
        date_to = f.date_to
        if f.period_id is not None:
            from app.models.academic_period import AcademicPeriod

            period = self.session.get(AcademicPeriod, f.period_id)
            if period:
                date_from = date_from or period.starts_on
                date_to = date_to or period.ends_on
        return self._as_dt(date_from, False), self._as_dt(date_to, True)

    @staticmethod
    def _as_dt(value, end: bool) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        return datetime.combine(value, time(23, 59, 59) if end else time.min)

    def _attendance(self, student_id, date_from, date_to) -> list[TimelineItem]:
        stmt = (
            select(AttendanceRecord, Lesson)
            .join(Lesson)
            .where(AttendanceRecord.student_id == student_id)
        )
        if date_from:
            stmt = stmt.where(Lesson.lesson_date >= date_from.date())
        if date_to:
            stmt = stmt.where(Lesson.lesson_date <= date_to.date())
        out = []
        for rec, lesson in self.session.execute(stmt):
            out.append(
                TimelineItem(
                    kind=TimelineKind.ATTENDANCE,
                    entity_id=rec.id,
                    occurred_at=datetime.combine(lesson.lesson_date, time.min),
                    title=f"Attendance: {rec.status}",
                    summary=rec.reason or rec.comment,
                    status=rec.status,
                )
            )
        return out

    def _academic(self, student_id, date_from, date_to) -> list[TimelineItem]:
        stmt = select(AcademicRecord).where(AcademicRecord.student_id == student_id)
        if date_from:
            stmt = stmt.where(AcademicRecord.record_date >= date_from.date())
        if date_to:
            stmt = stmt.where(AcademicRecord.record_date <= date_to.date())
        return [
            TimelineItem(
                kind=TimelineKind.ACADEMIC,
                entity_id=r.id,
                occurred_at=datetime.combine(r.record_date, time.min),
                title=f"Grade: {r.score if r.score is not None else r.text_result}",
                summary=r.comment,
                status=r.grade_scale,
            )
            for r in self.session.scalars(stmt)
        ]

    def _assignments(self, student_id, date_from, date_to) -> list[TimelineItem]:
        stmt = (
            select(Assignment)
            .join(AssignmentStudent)
            .where(AssignmentStudent.student_id == student_id)
        )
        if date_from:
            stmt = stmt.where(Assignment.due_date >= date_from.date())
        if date_to:
            stmt = stmt.where(Assignment.due_date <= date_to.date())
        return [
            TimelineItem(
                kind=TimelineKind.ASSIGNMENT,
                entity_id=a.id,
                occurred_at=datetime.combine(a.due_date, time.min),
                title=a.title,
                summary=a.description,
                status=a.effective_status,
            )
            for a in self.session.scalars(stmt).unique()
        ]

    def _duties(self, student_id, date_from, date_to) -> list[TimelineItem]:
        stmt = select(Duty).join(DutyStudent).where(DutyStudent.student_id == student_id)
        if date_from:
            stmt = stmt.where(Duty.duty_date >= date_from.date())
        if date_to:
            stmt = stmt.where(Duty.duty_date <= date_to.date())
        return [
            TimelineItem(
                kind=TimelineKind.DUTY,
                entity_id=d.id,
                occurred_at=datetime.combine(d.duty_date, time.min),
                title=d.duty_type or "Duty",
                summary=d.location,
                status=d.status,
            )
            for d in self.session.scalars(stmt).unique()
        ]

    def _events(self, student_id, date_from, date_to) -> list[TimelineItem]:
        stmt = select(Event).join(EventStudent).where(EventStudent.student_id == student_id)
        if date_from:
            stmt = stmt.where(Event.starts_at >= date_from)
        if date_to:
            stmt = stmt.where(Event.starts_at <= date_to)
        return [
            TimelineItem(
                kind=TimelineKind.EVENT,
                entity_id=e.id,
                occurred_at=e.starts_at,
                title=e.title,
                summary=e.location,
                status=e.status,
            )
            for e in self.session.scalars(stmt).unique()
        ]

    def _meetings(self, student_id, date_from, date_to) -> list[TimelineItem]:
        stmt = select(Meeting).join(MeetingStudent).where(MeetingStudent.student_id == student_id)
        if date_from:
            stmt = stmt.where(Meeting.scheduled_at >= date_from)
        if date_to:
            stmt = stmt.where(Meeting.scheduled_at <= date_to)
        return [
            TimelineItem(
                kind=TimelineKind.MEETING,
                entity_id=m.id,
                occurred_at=m.scheduled_at,
                title=m.topic,
                summary=m.result_summary,
                status=m.status,
            )
            for m in self.session.scalars(stmt).unique()
        ]

    def _logs(self, student_id, date_from, date_to) -> list[TimelineItem]:
        stmt = (
            select(CuratorLog)
            .join(CuratorLogStudent)
            .where(CuratorLogStudent.student_id == student_id)
        )
        if date_from:
            stmt = stmt.where(CuratorLog.occurred_at >= date_from)
        if date_to:
            stmt = stmt.where(CuratorLog.occurred_at <= date_to)
        return [
            TimelineItem(
                kind=TimelineKind.CURATOR_LOG,
                entity_id=c.id,
                occurred_at=c.occurred_at,
                title=c.title,
                summary=c.description[:200],
                status=c.category,
            )
            for c in self.session.scalars(stmt).unique()
        ]

    def _notes(self, student_id, date_from, date_to) -> list[TimelineItem]:
        stmt = select(Note).where(Note.student_id == student_id, Note.is_archived.is_(False))
        if date_from:
            stmt = stmt.where(Note.created_at >= date_from)
        if date_to:
            stmt = stmt.where(Note.created_at <= date_to)
        return [
            TimelineItem(
                kind=TimelineKind.NOTE,
                entity_id=n.id,
                occurred_at=n.created_at,
                title=n.title,
                summary=n.body[:200],
                status=n.category,
            )
            for n in self.session.scalars(stmt)
        ]
