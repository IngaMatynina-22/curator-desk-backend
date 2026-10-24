from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any

from sqlalchemy import select

from app.core.date_utils import utc_now
from app.core.enums import AssignmentStatus, DutyStatus, EventStatus, MeetingStatus
from app.models.assignment import Assignment
from app.models.associations import AssignmentStudent, DutyStudent, EventStudent, MeetingStudent
from app.models.duty import Duty
from app.models.event import Event
from app.models.meeting import Meeting
from app.services.base import BaseService


class CalendarService(BaseService):
    """Aggregates events, meetings, duties and overdue assignments."""

    def for_period(
        self,
        start: datetime | date,
        end: datetime | date,
        *,
        student_id: int | None = None,
    ) -> list[dict[str, Any]]:
        start_dt = self._as_datetime(start, end_of_day=False)
        end_dt = self._as_datetime(end, end_of_day=True)
        items: list[dict[str, Any]] = []
        items.extend(self._events(start_dt, end_dt, student_id))
        items.extend(self._meetings(start_dt, end_dt, student_id))
        items.extend(self._duties(start_dt.date(), end_dt.date(), student_id))
        items.extend(self._overdue_assignments(student_id))
        items.sort(key=lambda x: x["starts_at"])
        return items

    def for_day(self, day: date, *, student_id: int | None = None) -> list[dict[str, Any]]:
        return self.for_period(day, day, student_id=student_id)

    def for_week(self, day: date, *, student_id: int | None = None) -> list[dict[str, Any]]:
        start = day - timedelta(days=day.weekday())
        end = start + timedelta(days=6)
        return self.for_period(start, end, student_id=student_id)

    def for_month(self, year: int, month: int, *, student_id: int | None = None) -> list[dict[str, Any]]:
        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(year, month + 1, 1) - timedelta(days=1)
        return self.for_period(start, end, student_id=student_id)

    def upcoming(self, *, limit: int = 20, student_id: int | None = None) -> list[dict[str, Any]]:
        now = utc_now()
        end = now + timedelta(days=30)
        items = [i for i in self.for_period(now, end, student_id=student_id) if i["kind"] != "assignment_overdue"]
        return items[:limit]

    def without_responsible(self) -> list[dict[str, Any]]:
        events = self.session.scalars(
            select(Event).where(Event.status == EventStatus.PLANNED)
        ).all()
        result = []
        for event in events:
            if not event.responsible_ids:
                result.append(
                    {
                        "kind": "event",
                        "id": event.id,
                        "title": event.title,
                        "starts_at": event.starts_at,
                        "warning": "no responsible assigned",
                    }
                )
        return result

    def find_conflicts(
        self,
        date_from: datetime | date,
        date_to: datetime | date,
        student_id: int | None = None,
    ) -> list[dict[str, Any]]:
        items = [
            i
            for i in self.for_period(date_from, date_to, student_id=student_id)
            if i["kind"] in {"event", "meeting", "duty"}
        ]
        conflicts: list[dict[str, Any]] = []
        for i, a in enumerate(items):
            for b in items[i + 1 :]:
                if a["starts_at"] < b["ends_at"] and b["starts_at"] < a["ends_at"]:
                    if student_id is not None or self._share_student(a, b):
                        conflicts.append(
                            {
                                "left": a,
                                "right": b,
                                "message": f"{a['kind']}#{a['id']} overlaps {b['kind']}#{b['id']}",
                            }
                        )
        return conflicts

    def get_agenda(self, scope: str = "day", day: date | None = None) -> dict[str, Any]:
        day = day or date.today()
        if scope == "week":
            items = self.for_week(day)
        else:
            items = self.for_day(day)
        pending = 0
        try:
            from app.services.notification_service import NotificationService

            pending = NotificationService(self.session).count_pending()
        except Exception:
            pending = 0
        overdue = [i for i in items if i["kind"] == "assignment_overdue"]
        return {
            "scope": scope,
            "day": day.isoformat(),
            "items": items,
            "overdue_count": len(overdue),
            "pending_notifications": pending,
        }

    def reschedule_event(self, event_id: int, starts_at: datetime, ends_at: datetime):
        from app.services.event_service import EventService

        return EventService(self.session).update(
            event_id, {"starts_at": starts_at, "ends_at": ends_at}
        )

    def create_recurring_events(self, template: dict, rule: dict) -> list:
        """Create discrete Event rows from a simple recurrence rule.

        rule: {freq: 'daily'|'weekly', interval: 1, count: N} or {until: datetime}
        """
        import uuid

        from dateutil.rrule import DAILY, WEEKLY, rrule

        from app.services.event_service import EventService

        freq_map = {"daily": DAILY, "weekly": WEEKLY}
        freq = freq_map.get(str(rule.get("freq", "weekly")).lower(), WEEKLY)
        start = template["starts_at"]
        if isinstance(start, str):
            start = datetime.fromisoformat(start)
        end = template["ends_at"]
        if isinstance(end, str):
            end = datetime.fromisoformat(end)
        duration = end - start
        kwargs: dict[str, Any] = {
            "freq": freq,
            "interval": int(rule.get("interval", 1)),
            "dtstart": start,
        }
        if rule.get("count"):
            kwargs["count"] = int(rule["count"])
        elif rule.get("until"):
            until = rule["until"]
            if isinstance(until, str):
                until = datetime.fromisoformat(until)
            kwargs["until"] = until
        else:
            kwargs["count"] = 4

        group_id = str(uuid.uuid4())
        events_svc = EventService(self.session)
        created = []
        for occurrence in rrule(**kwargs):
            payload = dict(template)
            payload["starts_at"] = occurrence
            payload["ends_at"] = occurrence + duration
            payload.pop("recurrence_group_id", None)
            out = events_svc.create(payload)
            # stamp recurrence group without extra commit cycle
            entity = events_svc.repo.get_or_raise(out.id, "Event")
            entity.recurrence_group_id = group_id
            events_svc.flush()
            events_svc.commit()
            out = events_svc._to_out(entity)
            created.append(out)
        return created

    def _share_student(self, a: dict, b: dict) -> bool:
        # Without student filter, still report time overlaps of calendar items.
        return True

    def _events(self, start, end, student_id) -> list[dict[str, Any]]:
        stmt = select(Event).where(
            Event.starts_at <= end,
            Event.ends_at >= start,
            Event.status != EventStatus.CANCELLED,
        )
        if student_id is not None:
            stmt = stmt.join(EventStudent).where(EventStudent.student_id == student_id)
        return [
            {
                "kind": "event",
                "id": e.id,
                "title": e.title,
                "starts_at": e.starts_at,
                "ends_at": e.ends_at,
                "status": e.status,
            }
            for e in self.session.scalars(stmt).unique().all()
        ]

    def _meetings(self, start, end, student_id) -> list[dict[str, Any]]:
        stmt = select(Meeting).where(
            Meeting.scheduled_at >= start,
            Meeting.scheduled_at <= end,
            Meeting.status != MeetingStatus.CANCELLED,
        )
        if student_id is not None:
            stmt = stmt.join(MeetingStudent).where(MeetingStudent.student_id == student_id)
        return [
            {
                "kind": "meeting",
                "id": m.id,
                "title": m.topic,
                "starts_at": m.scheduled_at,
                "ends_at": m.scheduled_at,
                "status": m.status,
            }
            for m in self.session.scalars(stmt).unique().all()
        ]

    def _duties(self, start: date, end: date, student_id) -> list[dict[str, Any]]:
        stmt = select(Duty).where(
            Duty.duty_date >= start,
            Duty.duty_date <= end,
            Duty.status != DutyStatus.CANCELLED,
        )
        if student_id is not None:
            stmt = stmt.join(DutyStudent).where(DutyStudent.student_id == student_id)
        items = []
        for d in self.session.scalars(stmt).unique().all():
            starts = datetime.combine(d.duty_date, d.start_time or time(0, 0))
            ends = datetime.combine(d.duty_date, d.end_time or time(23, 59))
            items.append(
                {
                    "kind": "duty",
                    "id": d.id,
                    "title": d.duty_type or "Duty",
                    "starts_at": starts,
                    "ends_at": ends,
                    "status": d.status,
                }
            )
        return items

    def _overdue_assignments(self, student_id) -> list[dict[str, Any]]:
        today = date.today()
        stmt = select(Assignment).where(
            Assignment.due_date < today,
            Assignment.status.notin_([AssignmentStatus.DONE, AssignmentStatus.CANCELLED]),
        )
        if student_id is not None:
            stmt = stmt.join(AssignmentStudent).where(
                AssignmentStudent.student_id == student_id
            )
        return [
            {
                "kind": "assignment_overdue",
                "id": a.id,
                "title": a.title,
                "starts_at": datetime.combine(a.due_date, time(0, 0)),
                "ends_at": datetime.combine(a.due_date, time(23, 59)),
                "status": "overdue",
            }
            for a in self.session.scalars(stmt).unique().all()
        ]

    @staticmethod
    def _as_datetime(value: datetime | date, *, end_of_day: bool) -> datetime:
        if isinstance(value, datetime):
            return value
        return datetime.combine(value, time(23, 59, 59) if end_of_day else time(0, 0))
