from pathlib import Path

import pytest

from app.core.exceptions import ValidationError
from app.services.backup_service import BackupService
from tests.factories import seed_basic


def test_backup_restore_roundtrip(container, engine):
    seed_basic(container)
    container.session.commit()
    backup = container.backup.create_backup(label="test")
    assert backup.exists()

    # mutate then restore
    groups = container.groups.list({})
    assert groups.total == 1
    container.groups.archive(groups.items[0].id)

    container.backup.restore(backup, make_safety_backup=True)
    # reopen checks via integrity
    assert container.backup.verify_integrity(container.backup.database_path)


def test_corrupt_backup_rejected(container, tmp_path):
    bad = tmp_path / "bad.db"
    bad.write_text("not a database")
    with pytest.raises(ValidationError):
        container.backup.verify_integrity(bad)
