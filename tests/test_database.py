from sqlalchemy import inspect, text

from app.database.base import Base
from app.database.initialization import init_database


def test_schema_created(engine):
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    expected = {
        "academic_groups",
        "students",
        "subjects",
        "academic_records",
        "lessons",
        "attendance_records",
        "duties",
        "duty_students",
        "assignments",
        "assignment_students",
        "events",
        "event_students",
        "meetings",
        "meeting_students",
        "curator_logs",
        "curator_log_students",
        "notes",
        "attachments",
        "audit_logs",
        "academic_periods",
        "notifications",
        "app_settings",
        "import_jobs",
        "users",
    }
    assert expected.issubset(tables)


def test_foreign_keys_enabled(engine):
    with engine.connect() as conn:
        value = conn.execute(text("PRAGMA foreign_keys")).scalar()
        assert value == 1


def test_metadata_has_models():
    assert "students" in Base.metadata.tables
    assert "academic_groups" in Base.metadata.tables


def test_init_database_idempotent(engine):
    init_database(engine)
    init_database(engine)
    assert inspect(engine).has_table("students")
