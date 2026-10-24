from pathlib import Path

from app.core.exceptions import ValidationError
from tests.factories import make_group, make_student


def test_import_preview_and_execute(container, tmp_path):
    group = make_group(container)
    csv_path = tmp_path / "students.csv"
    csv_path.write_text(
        "student_number,last_name,first_name,email\n"
        "IMP-01,New,Student,a@b.com\n"
        "IMP-02,Other,Person,b@c.com\n",
        encoding="utf-8",
    )
    preview = container.imports.preview_import(csv_path, group_id=group.id)
    assert preview.valid is True
    assert preview.to_create == 2
    assert preview.job_id

    validated = container.imports.validate_import(preview.job_id)
    assert validated.valid is True
    executed = container.imports.execute_import(preview.job_id)
    assert executed.to_create == 2
    listed = container.students.list({"group_id": group.id})
    assert listed.total == 2


def test_import_skips_existing_number_no_fio_overwrite(container, tmp_path):
    group = make_group(container)
    make_student(container, group.id, "IMP-99", last_name="Exists", first_name="Already")
    csv_path = tmp_path / "dup.csv"
    csv_path.write_text(
        "student_number,last_name,first_name\n"
        "IMP-99,Exists,Already\n"
        "IMP-100,Exists,Already\n",
        encoding="utf-8",
    )
    preview = container.imports.preview_import(csv_path, group_id=group.id)
    assert preview.valid is True
    assert preview.to_create == 1
    assert any("FIO duplicate" in w for w in preview.warnings)
    container.imports.execute_import(preview.job_id)
    # original not overwritten; new number created
    assert container.students.list({"group_id": group.id}).total == 2


def test_import_requires_group(container, tmp_path):
    csv_path = tmp_path / "x.csv"
    csv_path.write_text("student_number,last_name,first_name\nA,B,C\n", encoding="utf-8")
    try:
        container.imports.preview_import(csv_path, group_id=None)
        assert False
    except ValidationError:
        pass
