from tests.factories import make_group


def test_audit_records_create_and_update(container):
    group = make_group(container)
    container.groups.update(group.id, {"curator_name": "New Curator"})
    entries = container.audit.for_entity("academic_group", group.id)
    ops = {e.operation for e in entries}
    assert "create" in ops
    assert "update" in ops
