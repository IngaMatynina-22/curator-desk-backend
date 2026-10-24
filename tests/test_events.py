from datetime import datetime, timedelta

from app.core.enums import EventStatus
from app.core.exceptions import ValidationError
from tests.factories import seed_basic


def test_event_overlap_and_cancel_rules(container):
    _, s1, _, _ = seed_basic(container)
    start = datetime.now().replace(microsecond=0)
    first = container.events.create(
        {
            "title": "Meeting A",
            "starts_at": start,
            "ends_at": start + timedelta(hours=2),
            "participant_ids": [s1.id],
            "responsible_ids": [s1.id],
        }
    )
    assert first.id

    second = container.events.create(
        {
            "title": "Meeting B",
            "starts_at": start + timedelta(hours=1),
            "ends_at": start + timedelta(hours=3),
        }
    )
    assert second.warnings

    cancelled = container.events.cancel(first.id)
    assert cancelled.status == EventStatus.CANCELLED
    try:
        container.events.update(first.id, {"status": EventStatus.COMPLETED})
        assert False
    except ValidationError:
        pass
