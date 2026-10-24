"""Storage path helpers."""

from pathlib import Path

from app.core.config import get_settings


def database_file() -> Path:
    return get_settings().database_path


def backups_dir() -> Path:
    return get_settings().backups_dir


def exports_dir() -> Path:
    return get_settings().exports_dir


def attachments_dir() -> Path:
    return get_settings().attachments_dir
