from datetime import datetime

from app.core.enums import MeetingStatus
from tests.factories import seed_basic


def test_meeting_history(container):
    _, s1, _, _ = seed_basic(container)
    meeting = container.meetings.create(
        {
            "scheduled_at": datetime.now().replace(microsecond=0),
            "topic": "Progress talk",
            "student_ids": [s1.id],
        }
    )
    completed = container.meetings.complete(meeting.id, "Agreed on plan")
    assert completed.status == MeetingStatus.COMPLETED
    assert completed.result_summary == "Agreed on plan"

    listed = container.meetings.list({"student_id": s1.id})
    assert listed.total == 1
