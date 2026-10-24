from app.core.enums import AttendanceStatus
from app.core.exceptions import ConflictError
from tests.factories import make_lesson, seed_basic


def test_attendance_unique_and_stats(container):
    _, s1, s2, subject = seed_basic(container)
    lesson = make_lesson(container, subject.id)

    container.attendance.mark(
        {
            "lesson_id": lesson.id,
            "student_id": s1.id,
            "status": AttendanceStatus.ABSENT,
        }
    )
    try:
        container.attendance.mark(
            {
                "lesson_id": lesson.id,
                "student_id": s1.id,
                "status": AttendanceStatus.PRESENT,
            }
        )
        assert False
    except ConflictError:
        pass

    container.attendance.bulk_mark(
        {
            "lesson_id": lesson.id,
            "marks": [
                {"student_id": s2.id, "status": AttendanceStatus.EXCUSED},
            ],
        }
    )

    stats = container.attendance.student_stats(s1.id)
    assert stats.absences == 1
    assert stats.hours_missed >= 2

    top = container.attendance.top_absentees()
    assert top[0][0] in {s1.id, s2.id}
