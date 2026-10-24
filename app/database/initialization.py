"""Create schema and prepare database."""

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.database.base import Base
from app.database.engine import create_db_engine, get_engine, set_engine
from app.database.session import configure_session_factory


def init_database(engine: Engine | None = None, *, create_schema: bool = True) -> Engine:
    # Import models so metadata is populated.
    import app.models  # noqa: F401

    if engine is None:
        engine = get_engine()
    else:
        set_engine(engine)

    configure_session_factory(engine)

    if create_schema:
        Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))
        result = conn.execute(text("PRAGMA foreign_key_check"))
        rows = result.fetchall()
        if rows:
            raise RuntimeError(f"Foreign key check failed: {rows}")
        conn.commit()

    return engine


def create_test_engine(url: str = "sqlite:///:memory:"):
    engine = create_db_engine(url=url)
    init_database(engine)
    return engine
