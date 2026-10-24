from datetime import date, timedelta

from app.core.enums import AssignmentStatus
from tests.factories import seed_basic


def test_assignment_overdue_computed(container):
    _, s1, _, _ = seed_basic(container)
    assignment = container.assignments.create(
        {
            "title": "Prepare report",
            "due_date": date.today() - timedelta(days=1),
            "student_ids": [s1.id],
            "status": AssignmentStatus.IN_PROGRESS,
        }
    )
    assert assignment.is_overdue is True
    assert assignment.effective_status == "overdue"

    overdue = container.assignments.overdue()
    assert any(a.id == assignment.id for a in overdue)

    done = container.assignments.complete(assignment.id, "done")
    assert done.status == AssignmentStatus.DONE
    assert done.is_overdue is False
