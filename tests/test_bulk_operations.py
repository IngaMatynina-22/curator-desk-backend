from datetime import date

from app.core.enums import AssignmentStatus, AttendanceStatus
from app.core.exceptions import NotFoundError
from tests.factories import make_lesson, seed_basic


def test_mark_group_attendance_preview_and_apply(container):
    group, s1, s2, subject = seed_basic(container)
    lesson = make_lesson(container, subject.id)
    preview = container.bulk.preview_group_attendance(lesson.id, group.id)
    assert preview.preview_only is True
    assert len(preview.details) == 2

    result = container.bulk.mark_group_attendance(
        {
            "lesson_id": lesson.id,
            "group_id": group.id,
            "default_status": AttendanceStatus.PRESENT,
        }
    )
    assert result.applied == 2
    listed = container.attendance.list({"student_id": s1.id})
    assert listed.total == 1


def test_bulk_update_assignments_rollback_on_error(container):
    _, s1, _, _ = seed_basic(container)
    a = container.assignments.create(
        {
            "title": "A1",
            "due_date": date.today(),
            "student_ids": [s1.id],
        }
    )
    result = container.bulk.bulk_update_assignments(
        {"ids": [a.id, 999999], "status": AssignmentStatus.DONE}
    )
    assert result.errors
    # failed mid-way should rollback — first assignment not done
    still = container.assignments.get(a.id)
    assert still.status != AssignmentStatus.DONE
