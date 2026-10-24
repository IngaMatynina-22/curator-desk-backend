from sqlalchemy import Select, or_

from app.models.student import Student


def apply_student_query(stmt: Select, query: str | None) -> Select:
    if not query:
        return stmt
    q = f"%{query.strip()}%"
    return stmt.where(
        or_(
            Student.last_name.ilike(q),
            Student.first_name.ilike(q),
            Student.student_number.ilike(q),
        )
    )
