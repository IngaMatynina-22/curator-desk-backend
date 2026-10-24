from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import func, select

from app.core.date_utils import utc_now
from app.core.enums import (
    AssignmentStatus,
    DutyStatus,
    EventStatus,
    MeetingStatus,
    NotificationKind,
)
from app.models.assignment import Assignment
from app.models.attendance import AttendanceRecord, Lesson
from app.models.duty import Duty
from app.models.event import Event
from app.models.meeting import Meeting
from app.models.student import Student
from app.services.base import BaseService
from app.services.notification_service import NotificationService
from app.services.settings_service import SettingsService


class ReminderService(BaseService):
    def __init__(self, session):
        super().__init__(session)
        self.notifications = NotificationService(session)
        self.settings = SettingsService(session)

    def generate(self) -> int:
        cfg = self.settings.get_reminder_settings()
        now = utc_now()
        created = 0
        created += self._events(now, cfg.event_hours_before)
        created += self._meetings(now, cfg.meeting_hours_before)
        created += self._duties(now, cfg.duty_hours_before)
        created += self._assignments(now, cfg.assignment_hours_before)
        if cfg.check_missing_attendance:
            created += self._missing_attendance(now)
        return created

    def _events(self, now: datetime, hours: int) -> int:
        window_end = now + timedelta(hours=hours)
        events = self.session.scalars(
            select(Event).where(
                Event.status == EventStatus.PLANNED,
                Event.starts_at >= now,
                Event.starts_at <= window_end,
            )
        ).all()
        for e in events:
            self.notifications.upsert(
                kind=NotificationKind.EVENT_UPCOMING,
                source_type="event",
                source_id=e.id,
                title=f"Upcoming event: {e.title}",
                body=e.location,
                due_at=e.starts_at,
            )
        return len(events)

    def _meetings(self, now: datetime, hours: int) -> int:
        window_end = now + timedelta(hours=hours)
        meetings = self.session.scalars(
            select(Meeting).where(
                Meeting.status == MeetingStatus.PLANNED,
                Meeting.scheduled_at >= now,
                Meeting.scheduled_at <= window_end,
            )
        ).all()
        for m in meetings:
            self.notifications.upsert(
                kind=NotificationKind.MEETING_UPCOMING,
                source_type="meeting",
                source_id=m.id,
                title=f"Upcoming meeting: {m.topic}",
                due_at=m.scheduled_at,
            )
        return len(meetings)

    def _duties(self, now: datetime, hours: int) -> int:
        today = date.today()
        until = (now + timedelta(hours=hours)).date()
        duties = self.session.scalars(
            select(Duty).where(
                Duty.status == DutyStatus.PLANNED,
                Duty.duty_date >= today,
                Duty.duty_date <= until,
            )
        ).all()
        for d in duties:
            due = datetime.combine(d.duty_date, d.start_time) if d.start_time else datetime.combine(d.duty_date, datetime.min.time())
            self.notifications.upsert(
                kind=NotificationKind.DUTY_UPCOMING,
                source_type="duty",
                source_id=d.id,
                title=f"Upcoming duty: {d.duty_type or 'duty'}",
                body=d.location,
                due_at=due,
            )
        return len(duties)

    def _assignments(self, now: datetime, hours: int) -> int:
        today = date.today()
        due_until = (now + timedelta(hours=hours)).date()
        count = 0
        upcoming = self.session.scalars(
            select(Assignment).where(
                Assignment.status.notin_([AssignmentStatus.DONE, AssignmentStatus.CANCELLED]),
                Assignment.due_date >= today,
                Assignment.due_date <= due_until,
            )
        ).all()
        for a in upcoming:
            self.notifications.upsert(
                kind=NotificationKind.ASSIGNMENT_DUE,
                source_type="assignment",
                source_id=a.id,
                title=f"Assignment due: {a.title}",
                due_at=datetime.combine(a.due_date, datetime.min.time()),
            )
            count += 1
        overdue = self.session.scalars(
            select(Assignment).where(
                Assignment.status.notin_([AssignmentStatus.DONE, AssignmentStatus.CANCELLED]),
                Assignment.due_date < today,
            )
        ).all()
        for a in overdue:
            self.notifications.upsert(
                kind=NotificationKind.ASSIGNMENT_OVERDUE,
                source_type="assignment",
                source_id=a.id,
                title=f"Overdue assignment: {a.title}",
                due_at=datetime.combine(a.due_date, datetime.min.time()),
            )
            count += 1
        return count

    def _missing_attendance(self, now: datetime) -> int:
        # Lessons today/yesterday with students in groups but no marks
        today = date.today()
        lessons = self.session.scalars(
            select(Lesson).where(Lesson.lesson_date >= today - timedelta(days=1), Lesson.lesson_date <= today)
        ).all()
        count = 0
        for lesson in lessons:
            marked = int(
                self.session.scalar(
                    select(func.count()).where(AttendanceRecord.lesson_id == lesson.id)
                )
                or 0
            )
            if marked == 0:
                self.notifications.upsert(
                    kind=NotificationKind.ATTENDANCE_MISSING,
                    source_type="lesson",
                    source_id=lesson.id,
                    title=f"Missing attendance for lesson on {lesson.lesson_date}",
                    due_at=datetime.combine(lesson.lesson_date, datetime.min.time()),
                )
                count += 1
        return count
