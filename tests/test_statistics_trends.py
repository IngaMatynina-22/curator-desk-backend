from datetime import date, timedelta

from app.core.enums import AttendanceStatus
from tests.factories import make_lesson, seed_basic


def test_attendance_trend_and_compare_periods(container):
    group, s1, _, subject = seed_basic(container)
    lesson = make_lesson(container, subject.id, lesson_date=date.today())
    container.attendance.mark(
        {"lesson_id": lesson.id, "student_id": s1.id, "status": AttendanceStatus.ABSENT}
    )
    trend = container.statistics.get_attendance_trend(
        granularity="week",
        date_from=date.today() - timedelta(days=7),
        date_to=date.today(),
        group_id=group.id,
    )
    assert trend
    assert trend[0].absences >= 1

    cmp = container.statistics.compare_periods(
        {"date_from": date.today() - timedelta(days=30), "date_to": date.today()},
        {"date_from": date.today() - timedelta(days=60), "date_to": date.today() - timedelta(days=31)},
    )
    assert "absences" in cmp.deltas

    overdue = container.statistics.get_overdue_summary()
    assert overdue.overdue_count >= 0
    activity = container.statistics.get_activity_summary()
    assert activity.events_planned >= 0
