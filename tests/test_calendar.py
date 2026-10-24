from datetime import date, datetime, timedelta

from app.core.enums import AssignmentStatus
from tests.factories import seed_basic


def test_calendar_aggregates(container):
    _, s1, _, _ = seed_basic(container)
    start = datetime.now().replace(microsecond=0)
    container.events.create(
        {
            "title": "Open day",
            "starts_at": start,
            "ends_at": start + timedelta(hours=1),
            "participant_ids": [s1.id],
        }
    )
    container.duties.create({"duty_date": date.today(), "student_ids": [s1.id]})
    container.assignments.create(
        {
            "title": "Late task",
            "due_date": date.today() - timedelta(days=2),
            "student_ids": [s1.id],
            "status": AssignmentStatus.NEW,
        }
    )

    day = container.calendar.for_day(date.today(), student_id=s1.id)
    kinds = {item["kind"] for item in day}
    assert "event" in kinds
    assert "duty" in kinds
    assert "assignment_overdue" in kinds
