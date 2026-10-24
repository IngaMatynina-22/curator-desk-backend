from datetime import date

from tests.factories import seed_basic


def test_assignment_update_writes_field_diffs(container):
    _, s1, _, _ = seed_basic(container)
    a = container.assignments.create(
        {"title": "Task", "due_date": date.today(), "student_ids": [s1.id]}
    )
    container.assignments.update(a.id, {"title": "Task renamed"})
    diffs = container.audit.diff_view("assignment", a.id)
    assert any(d["field"] == "title" and d["new"] == "Task renamed" for d in diffs)


def test_period_crud(container):
    period = container.periods.create(
        {
            "name": "Fall 2025",
            "academic_year": "2025/2026",
            "starts_on": date(2025, 9, 1),
            "ends_on": date(2026, 1, 31),
            "is_current": True,
        }
    )
    assert period.is_current is True
    other = container.periods.create(
        {
            "name": "Spring 2026",
            "academic_year": "2025/2026",
            "starts_on": date(2026, 2, 1),
            "ends_on": date(2026, 6, 30),
            "is_current": True,
        }
    )
    assert other.is_current is True
    first = container.periods.get(period.id)
    assert first.is_current is False
