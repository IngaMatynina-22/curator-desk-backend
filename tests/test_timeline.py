from datetime import date, datetime, timedelta

from app.core.enums import AssignmentStatus, AttendanceStatus, TimelineKind
from tests.factories import make_lesson, seed_basic


def test_student_timeline_aggregates_and_filters(container):
    group, s1, _, subject = seed_basic(container)
    lesson = make_lesson(container, subject.id)
    container.attendance.mark(
        {"lesson_id": lesson.id, "student_id": s1.id, "status": AttendanceStatus.ABSENT}
    )
    container.assignments.create(
        {
            "title": "Essay",
            "due_date": date.today() + timedelta(days=2),
            "student_ids": [s1.id],
            "status": AssignmentStatus.NEW,
        }
    )
    container.events.create(
        {
            "title": "Assembly",
            "starts_at": datetime.now().replace(microsecond=0),
            "ends_at": datetime.now().replace(microsecond=0) + timedelta(hours=1),
            "participant_ids": [s1.id],
        }
    )

    all_items = container.timeline.get_timeline(s1.id)
    kinds = {i.kind for i in all_items.items}
    assert TimelineKind.ATTENDANCE in kinds
    assert TimelineKind.ASSIGNMENT in kinds
    assert TimelineKind.EVENT in kinds

    only_att = container.timeline.get_timeline(s1.id, types=[TimelineKind.ATTENDANCE])
    assert only_att.total == 1
    assert only_att.items[0].kind == TimelineKind.ATTENDANCE
