from datetime import date, time

from tests.factories import seed_basic


def test_duty_overlap_warning(container):
    _, s1, _, _ = seed_basic(container)
    first = container.duties.create(
        {
            "duty_date": date.today(),
            "start_time": time(9, 0),
            "end_time": time(11, 0),
            "student_ids": [s1.id],
            "duty_type": "classroom",
        }
    )
    assert first.warnings == []

    second = container.duties.create(
        {
            "duty_date": date.today(),
            "start_time": time(10, 0),
            "end_time": time(12, 0),
            "student_ids": [s1.id],
            "duty_type": "hallway",
        }
    )
    assert second.warnings
    listed = container.duties.list({"student_id": s1.id})
    assert listed.total == 2
