"""Application entry bootstrap for backend / future GUI."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.container import create_container
from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.database.engine import set_engine
from app.database.initialization import init_database
from app.database.seed import DEMO_PASSWORD, DEMO_USERNAME, seed_full
from app.database.session import SessionLocal, configure_session_factory, get_session


def reset_database() -> None:
    settings = get_settings()
    db_path = Path(settings.database_path)
    set_engine(None)
    if db_path.exists():
        db_path.unlink()
        for suffix in ("-wal", "-shm", "-journal"):
            side = Path(str(db_path) + suffix)
            if side.exists():
                side.unlink()
    settings.ensure_dirs()
    init_database()


def bootstrap(*, seed: bool = False, reset_db: bool = False):
    setup_logging()
    if reset_db:
        reset_database()
    else:
        init_database()
    container = create_container(init_db=False)
    if seed:
        result = seed_full(container.session)
        print(f"Seed: {result}")
        if not result.get("skipped"):
            container.auth.login({"username": DEMO_USERNAME, "password": DEMO_PASSWORD})
    return container


def main() -> None:
    parser = argparse.ArgumentParser(description="CuratorDesk backend")
    parser.add_argument("--seed", action="store_true", help="Load full demo dataset")
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Delete SQLite database and recreate schema",
    )
    args = parser.parse_args()
    container = bootstrap(seed=args.seed, reset_db=args.reset_db)
    user = container.auth.current_user()
    user_label = user.username if user else "(not logged in)"
    print(
        f"CuratorDesk backend ready. Groups: {container.groups.count()} | "
        f"Students: {container.students.list({}).total} | User: {user_label}"
    )
    if args.seed and not user:
        print(f"Demo login: {DEMO_USERNAME} / {DEMO_PASSWORD}")
    container.close()


if __name__ == "__main__":
    main()
