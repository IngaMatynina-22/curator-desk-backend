from sqlalchemy import Select


def apply_date_bounds(stmt: Select, column, date_from=None, date_to=None) -> Select:
    if date_from is not None:
        stmt = stmt.where(column >= date_from)
    if date_to is not None:
        stmt = stmt.where(column <= date_to)
    return stmt
