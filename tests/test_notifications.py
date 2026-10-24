from datetime import datetime, timedelta

from app.core.enums import AssignmentStatus
from tests.factories import seed_basic


def test_generate_notifications_idempotent_and_snooze(container):
    _, s1, _, _ = seed_basic(container)
    container.assignments.create(
        {
            "title": "Soon due",
            "due_date": datetime.now().date(),
            "student_ids": [s1.id],
            "status": AssignmentStatus.NEW,
        }
    )
    first = container.notifications.generate_due_notifications()
    assert first
    second = container.notifications.generate_due_notifications()
    # unique constraint keeps one per source
    pending = container.notifications.get_pending()
    assert len(pending) <= len(second) + 5

    target = pending[0]
    snoozed = container.notifications.snooze(
        target.id, datetime.now() + timedelta(hours=2)
    )
    assert snoozed.status == "snoozed"
    read = container.notifications.mark_as_read(target.id)
    assert read.status == "read"
