# CuratorDesk

Local academic group CRM backend (Python + SQLAlchemy 2 + SQLite + Pydantic).

GUI (PyQt6) should call services through `ServiceContainer` — never SQL directly.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e ".[dev]"
```

## Bootstrap

Пересоздать БД и загрузить полный демо-seed + логин:

```powershell
python -m app.main --reset-db --seed
```

Демо-акаунт: `curator` / `curator123`

Обычный старт (без пересоздания):

```powershell
python -m app.main
```

```python
from app.container import create_container

c = create_container()

# реєстрація / вхід
c.auth.register({
    "username": "anna",
    "password": "secret12",
    "full_name": "Anna Curator",
})
c.auth.login({"username": "curator", "password": "curator123"})
print(c.auth.current_user())

print(c.statistics.overview())
c.close()
```

## Architecture

`GUI → ServiceContainer → Services → Repositories → SQLite`

Modules: groups, students, academic, attendance, duties, assignments, events, meetings, curator logs, notes, search, calendar, statistics, reports, backup, audit.

### Backend v2 (daily curator tools)

| Container attr | Purpose |
|---|---|
| `timeline` | Unified student chronology (no duplicate table) |
| `notifications` / `reminders` | Due reminders, snooze/read, idempotent generate |
| `bulk` | Group attendance, bulk assignments/duties/archive with preview + transaction |
| `calendar.find_conflicts` / `get_agenda` / `create_recurring_events` / `reschedule_event` | Schedule control |
| `statistics.get_attendance_trend` / `compare_periods` / … | Trends without subjective labels |
| `imports` | CSV/XLSX student import with preview (no FIO overwrite) |
| `periods` | Academic periods |
| `integrity` | Read-only data integrity report |
| `settings` | Reminder intervals and app defaults |

```python
c = create_container()
c.notifications.generate_due_notifications()
c.timeline.get_timeline(student_id=1)
c.bulk.preview_group_attendance(lesson_id=1, group_id=1)
c.calendar.get_agenda("week")
```

## Tests


```bash
pytest -q
pytest --cov=app --cov-report=term-missing
```

## Storage

- DB: `app/storage/database/curatordesk.db`
- Backups: `app/storage/backups/`
- Exports: `app/storage/exports/`

## Migrations

Schema is created via `init_database()` (`Base.metadata.create_all`). Alembic baseline lives in `alembic/versions/` for future schema changes.
