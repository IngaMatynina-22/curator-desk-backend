from datetime import datetime

from app.core.enums import CuratorLogCategory
from app.core.exceptions import ConflictError, ValidationError
from tests.factories import seed_basic


def test_curator_log_no_duplicate_for_meeting(container):
    _, s1, _, _ = seed_basic(container)
    meeting = container.meetings.create(
        {
            "scheduled_at": datetime.now().replace(microsecond=0),
            "topic": "Talk",
            "student_ids": [s1.id],
        }
    )
    entry = container.curator_logs.create(
        {
            "occurred_at": datetime.now().replace(microsecond=0),
            "category": CuratorLogCategory.STUDENT_COMMUNICATION,
            "title": "After meeting",
            "description": "Discussed attendance",
            "meeting_id": meeting.id,
            "student_ids": [s1.id],
        }
    )
    assert entry.id
    try:
        container.curator_logs.create(
            {
                "occurred_at": datetime.now().replace(microsecond=0),
                "title": "Dup",
                "description": "x",
                "meeting_id": meeting.id,
            }
        )
        assert False
    except ConflictError:
        pass

    found = container.curator_logs.list({"query": "attendance"})
    assert found.total >= 1


def test_curator_log_rejects_blank_description(container):
    try:
        container.curator_logs.create(
            {
                "occurred_at": datetime.now().replace(microsecond=0),
                "title": "Запис",
                "description": "   ",
            }
        )
        assert False
    except ValidationError:
        pass
