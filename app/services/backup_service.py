from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import DatabaseError, ValidationError


class BackupService:
    def __init__(self, session: Session | None = None, database_path: Path | None = None):
        self.session = session
        settings = get_settings()
        self.database_path = Path(database_path or settings.database_path)
        self.backups_dir = settings.backups_dir
        self.backups_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, label: str | None = None) -> Path:
        if not self.database_path.exists():
            raise DatabaseError(f"database not found: {self.database_path}")
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = f"_{label}" if label else ""
        dest = self.backups_dir / f"curatordesk_{stamp}{suffix}.db"
        try:
            with sqlite3.connect(self.database_path) as src:
                with sqlite3.connect(dest) as dst:
                    src.backup(dst)
        except sqlite3.Error as exc:
            raise DatabaseError(f"backup failed: {exc}") from exc
        self.verify_integrity(dest)
        return dest

    def restore(self, backup_path: Path | str, *, make_safety_backup: bool = True) -> Path:
        backup = Path(backup_path)
        if not backup.exists():
            raise ValidationError(f"backup not found: {backup}")
        self.verify_integrity(backup)
        safety = None
        if make_safety_backup and self.database_path.exists():
            safety = self.create_backup(label="pre_restore")
        try:
            with sqlite3.connect(backup) as src:
                with sqlite3.connect(self.database_path) as dst:
                    src.backup(dst)
        except sqlite3.Error as exc:
            raise DatabaseError(f"restore failed: {exc}") from exc
        self.verify_integrity(self.database_path)
        return safety or self.database_path

    def verify_integrity(self, db_path: Path | str) -> bool:
        path = Path(db_path)
        if not path.exists() or path.stat().st_size == 0:
            raise ValidationError(f"invalid backup file: {path}")
        try:
            with sqlite3.connect(path) as conn:
                row = conn.execute("PRAGMA integrity_check").fetchone()
                if not row or row[0] != "ok":
                    raise ValidationError(f"integrity check failed for {path}: {row}")
                conn.execute("PRAGMA foreign_keys=ON")
        except sqlite3.DatabaseError as exc:
            raise ValidationError(f"corrupt database: {exc}") from exc
        return True

    def list_backups(self) -> list[Path]:
        return sorted(self.backups_dir.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
