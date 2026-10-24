from sqlalchemy import Select

from app.models.attendance import AttendanceRecord, Lesson


def apply_attendance_period(stmt: Select, date_from=None, date_to=None) -> Select:
    if date_from is not None:
        stmt = stmt.where(Lesson.lesson_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Lesson.lesson_date <= date_to)
    return stmt


def apply_attendance_status(stmt: Select, status: str | None) -> Select:
    if status:
        stmt = stmt.where(AttendanceRecord.status == status)
    return stmt
