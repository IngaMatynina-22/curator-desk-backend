from tests.factories import make_group, make_student, seed_basic


def test_integrity_ok_on_clean_db(container):
    seed_basic(container)
    report = container.integrity.run_checks()
    assert report.ok is True
    assert report.issues == []


def test_integrity_warns_active_in_archived_group(container):
    group = make_group(container)
    student = make_student(container, group.id, "ARC-1")
    container.groups.archive(group.id)
    report = container.integrity.run_checks()
    codes = {i.code for i in report.issues}
    assert "active_student_in_archived_group" in codes
    assert any(i.entity_id == student.id for i in report.issues)
