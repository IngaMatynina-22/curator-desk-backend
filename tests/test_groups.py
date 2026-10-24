from app.core.exceptions import NotFoundError, ValidationError
from tests.factories import make_group


def test_group_crud(container):
    group = make_group(container, name="ІПЗ-22")
    assert group.id > 0
    assert group.active_students == 0

    updated = container.groups.update(group.id, {"course": 4})
    assert updated.course == 4

    listed = container.groups.list({"query": "ІПЗ"})
    assert listed.total == 1

    archived = container.groups.archive(group.id)
    assert archived.is_archived is True
    restored = container.groups.restore(group.id)
    assert restored.is_archived is False


def test_group_validation(container):
    try:
        container.groups.create({"name": "", "specialty": "x", "course": 1, "academic_year": "2025"})
        assert False
    except ValidationError:
        pass


def test_group_not_found(container):
    try:
        container.groups.get(9999)
        assert False
    except NotFoundError:
        pass
