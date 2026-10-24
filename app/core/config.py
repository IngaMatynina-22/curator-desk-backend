"""Application configuration."""

from dataclasses import dataclass, field
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_STORAGE = _ROOT / "app" / "storage"


@dataclass
class Settings:
    app_name: str = "CuratorDesk"
    operator_name: str = "curator"
    database_path: Path = field(default_factory=lambda: _STORAGE / "database" / "curatordesk.db")
    backups_dir: Path = field(default_factory=lambda: _STORAGE / "backups")
    exports_dir: Path = field(default_factory=lambda: _STORAGE / "exports")
    attachments_dir: Path = field(default_factory=lambda: _STORAGE / "attachments")
    default_page_size: int = 50
    max_page_size: int = 500
    echo_sql: bool = False

    @property
    def database_url(self) -> str:
        path = self.database_path.resolve().as_posix()
        return f"sqlite:///{path}"

    def ensure_dirs(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.attachments_dir.mkdir(parents=True, exist_ok=True)


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_dirs()
    return _settings


def configure_settings(**kwargs) -> Settings:
    global _settings
    base = Settings()
    for key, value in kwargs.items():
        if not hasattr(base, key):
            raise AttributeError(f"Unknown setting: {key}")
        setattr(base, key, value)
    base.ensure_dirs()
    _settings = base
    return _settings
