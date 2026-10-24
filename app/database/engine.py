"""SQLite engine with foreign keys enabled."""

from collections.abc import Callable

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings

_engine: Engine | None = None


def _enable_foreign_keys(dbapi_conn, _connection_record) -> None:
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_db_engine(settings: Settings | None = None, *, url: str | None = None) -> Engine:
    settings = settings or get_settings()
    db_url = url or settings.database_url
    connect_args: dict = {"check_same_thread": False}
    kwargs: dict = {"echo": settings.echo_sql, "future": True}

    if db_url.startswith("sqlite") and ":memory:" in db_url:
        kwargs["poolclass"] = StaticPool

    engine = create_engine(db_url, connect_args=connect_args, **kwargs)
    event.listen(engine, "connect", _enable_foreign_keys)
    return engine


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_db_engine()
    return _engine


def set_engine(engine: Engine | None) -> None:
    global _engine
    _engine = engine
