from datetime import datetime, timedelta

from tests.factories import seed_basic


def test_find_conflicts_and_agenda(container):
    _, s1, _, _ = seed_basic(container)
    start = datetime.now().replace(microsecond=0)
    container.events.create(
        {
            "title": "A",
            "starts_at": start,
            "ends_at": start + timedelta(hours=2),
            "participant_ids": [s1.id],
        }
    )
    container.events.create(
        {
            "title": "B",
            "starts_at": start + timedelta(hours=1),
            "ends_at": start + timedelta(hours=3),
            "participant_ids": [s1.id],
        }
    )
    conflicts = container.calendar.find_conflicts(start.date(), start.date(), student_id=s1.id)
    assert conflicts
    agenda = container.calendar.get_agenda("day", start.date())
    assert agenda["items"]
