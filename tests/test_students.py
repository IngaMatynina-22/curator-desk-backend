from datetime import date, timedelta

from app.core.exceptions import ConflictError, ValidationError
from tests.factories import make_group, make_student, seed_basic


def test_student_crud_and_search(container):
    group, s1, s2, _ = seed_basic(container)
    found = container.students.list({"query": "Ivanov"})
    assert found.total == 1
    assert found.items[0].full_name.startswith("Ivanov")

    updated = container.students.update(s1.id, {"phone": "+380501112233"})
    assert updated.phone == "+380501112233"

    archived = container.students.archive(s2.id)
    assert archived.is_archived is True
    active = container.students.list({"group_id": group.id})
    assert active.total == 1


def test_student_number_unique(container):
    group = make_group(container)
    make_student(container, group.id, "DUP-1")
    try:
        make_student(container, group.id, "DUP-1", last_name="Other")
        assert False
    except ConflictError:
        pass


def test_birth_date_not_future(container):
    group = make_group(container)
    try:
        make_student(
            container,
            group.id,
            "FUT-1",
            birth_date=date.today() + timedelta(days=1),
        )
        assert False
    except ValidationError:
        pass


def test_student_summary(container):
    _, s1, _, _ = seed_basic(container)
    summary = container.students.summary(s1.id)
    assert summary.student.id == s1.id
    assert summary.attendance_absences == 0
