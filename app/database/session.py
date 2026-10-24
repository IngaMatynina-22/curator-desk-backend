"""Session factory and helpers."""

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.orm import Session, sessionmaker

from app.database.engine import get_engine

SessionLocal = sessionmaker(autoflush=False, autocommit=False, expire_on_commit=False)


def configure_session_factory(engine=None) -> None:
    SessionLocal.configure(bind=engine or get_engine())


def get_session() -> Session:
    if SessionLocal.kw.get("bind") is None:
        configure_session_factory()
    return SessionLocal()


@contextmanager
def session_scope() -> Iterator[Session]:
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
