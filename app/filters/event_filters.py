from sqlalchemy import Select, or_

from app.models.event import Event


def apply_event_query(stmt: Select, query: str | None) -> Select:
    if not query:
        return stmt
    q = f"%{query}%"
    return stmt.where(or_(Event.title.ilike(q), Event.description.ilike(q)))
