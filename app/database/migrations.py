"""Thin Alembic helpers."""

from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.config import get_settings

_ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


def get_alembic_config(database_url: str | None = None) -> Config:
    cfg = Config(str(_ALEMBIC_INI))
    url = database_url or get_settings().database_url
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def upgrade_head(database_url: str | None = None) -> None:
    command.upgrade(get_alembic_config(database_url), "head")


def revision_autogenerate(message: str, database_url: str | None = None) -> None:
    command.revision(get_alembic_config(database_url), message=message, autogenerate=True)
