# CuratorDesk: повний функціональний довідник

## 1. Призначення проєкту

CuratorDesk — локальна CRM-система для кураторської роботи з академічною групою.
Backend написаний на Python і використовує:

- SQLAlchemy 2 для роботи з SQLite;
- Pydantic для вхідних/вихідних моделей;
- SQLite як локальне сховище;
- структуру `GUI -> ServiceContainer -> Services -> Repositories -> SQLite`;
- pytest для тестів;
- Alembic як основу майбутніх міграцій.

GUI не повинна звертатись до SQL напряму. Усі операції виконуються через
`app.container.ServiceContainer`.

## 2. Точки входу та налаштування

Базова конфігурація знаходиться в `app/core/config.py`.
Основні каталоги створюються автоматично:

| Дані | Шлях |
|---|---|
| База даних | `app/storage/database/curatordesk.db` |
| Резервні копії | `app/storage/backups/` |
| Експорт | `app/storage/exports/` |

Запуск і відновлення даних:

```powershell
# звичайний запуск
python -m app.main

# повне пересоздання БД і завантаження демо-даних
python -m app.main --reset-db --seed

# демо-користувач
curator / curator123
```

Bootstrap виконує перевірку/створення схеми, налаштовує логування і за
потреби завантажує seed:

```python
def bootstrap(*, seed: bool = False, reset_db: bool = False):
    setup_logging()
    if reset_db:
        reset_database()
    else:
        init_database()

    container = create_container(init_db=False)
    if seed:
        result = seed_full(container.session)
        if not result.get("skipped"):
            container.auth.login({
                "username": DEMO_USERNAME,
                "password": DEMO_PASSWORD,
            })
    return container
```

## 3. Головний контейнер сервісів

`app/container.py` є єдиною точкою доступу для GUI та скриптів.

```python
class ServiceContainer:
    def __init__(self, session: Session):
        self.session = session
        self.auth = AuthService(session)
        self.groups = GroupService(session)
        self.students = StudentService(session)
        self.academic = AcademicService(session)
        self.attendance = AttendanceService(session)
        self.duties = DutyService(session)
        self.assignments = AssignmentService(session)
        self.events = EventService(session)
        self.meetings = MeetingService(session)
        self.curator_logs = CuratorLogService(session)
        self.notes = NoteService(session)
        self.search = SearchService(session)
        self.calendar = CalendarService(session)
        self.statistics = StatisticsService(session)
        self.reports = ReportService(session)
        self.audit = AuditService(session)
        self.backup = BackupService(session=session)
        self.timeline = StudentTimelineService(session)
        self.periods = PeriodService(session)
        self.integrity = IntegrityService(session)
        self.notifications = NotificationService(session)
        self.reminders = ReminderService(session)
        self.bulk = BulkOperationService(session)
        self.imports = ImportService(session)
        self.settings = SettingsService(session)

    def close(self) -> None:
        self.session.close()


def create_container(*, init_db: bool = True) -> ServiceContainer:
    get_settings().ensure_dirs()
    if init_db:
        init_database()
    return ServiceContainer(get_session())
```

Приклад використання:

```python
c = create_container()
c.auth.login({
    "username": "curator",
    "password": "curator123",
})
print(c.auth.current_user())
print(c.statistics.overview())
c.close()
```

## 4. Архітектура та загальні правила

### 4.1 Базовий сервіс

Усі основні сервіси успадковують `BaseService`. Він стандартизує commit,
rollback, а також запис аудиту:

```python
class BaseService:
    def commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError(str(exc.orig) if exc.orig else str(exc)) from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError(str(exc)) from exc

    def audit(self, entity_id, operation, changes=None) -> None:
        write_audit(
            self.session,
            entity_type=self.entity_type,
            entity_id=entity_id,
            operation=operation,
            changes=changes,
        )

    def run_in_transaction(self, fn):
        try:
            result = fn()
            self.commit()
            return result
        except (ValidationError, ConflictError, DatabaseError):
            self.session.rollback()
            raise
        except Exception:
            self.session.rollback()
            raise
```

`run_in_transaction` гарантує rollback при помилці. Сервісні методи приймають
Pydantic-схему або словник і перетворюють словник у схему через
`parse_schema`.

### 4.2 Репозиторії

Репозиторії інкапсулюють базові CRUD-операції:

```python
class BaseRepository(Generic[ModelT]):
    def get(self, entity_id):
        return self.session.get(self.model, entity_id)

    def get_or_raise(self, entity_id, label=None):
        entity = self.get(entity_id)
        if entity is None:
            raise NotFoundError(f"{label or self.model.__name__} id={entity_id} not found")
        return entity

    def add(self, entity):
        self.session.add(entity)
        self.session.flush()
        return entity

    def archive(self, entity):
        entity.is_archived = True
        self.session.flush()
        return entity

    def restore(self, entity):
        entity.is_archived = False
        self.session.flush()
        return entity
```

Спеціалізовані репозиторії додають пошук, фільтрацію, пагінацію та перевірки:
`GroupRepository`, `StudentRepository`, `AcademicRecordRepository`,
`AttendanceRepository`, `AssignmentRepository`, `DutyRepository`,
`EventRepository`, `MeetingRepository`, `CuratorLogRepository`,
`NoteRepository`, `UserRepository`, `PeriodRepository`, `AuditRepository`.

### 4.3 Помилки

`app/core/exceptions.py` містить типові доменні винятки:

- `ValidationError`;
- `NotFoundError`;
- `ConflictError`;
- `DatabaseError`;
- `AuthError`.

Вони дозволяють GUI обробляти помилки за типом, а не за текстом SQLAlchemy.

## 5. Модель даних

Основні сутності SQLAlchemy знаходяться в `app/models/`:

| Модель | Основне призначення |
|---|---|
| `User` | Користувачі, ролі та пароль |
| `AcademicGroup` | Академічні групи |
| `Student` | Студенти групи |
| `AcademicPeriod` | Навчальні періоди |
| `Subject` | Навчальні предмети |
| `AcademicRecord` | Оцінки й текстові результати |
| `Lesson` | Заняття |
| `AttendanceRecord` | Відвідуваність студентів |
| `Duty` | Чергування |
| `Assignment` | Завдання |
| `Event` | Події календаря |
| `Meeting` | Зустрічі |
| `CuratorLog` | Записи кураторського журналу |
| `Note` | Нотатки про студентів |
| `Notification` | Сповіщення |
| `AppSetting` | Налаштування застосунку |
| `AuditLog` | Аудит змін |
| `Attachment` | Файлові вкладення |
| `ImportJob` | Стан імпорту студентів |

Багато сутностей мають поля часу створення/оновлення через `TimestampMixin`
та підтримку soft-archive через `SoftArchiveMixin`.

### 5.1 Зв’язки many-to-many

Через асоціативні моделі реалізовані зв’язки студентів із:

- чергуваннями;
- завданнями;
- подіями;
- зустрічями;
- записами кураторського журналу.

Кожна така сутність містить ідентифікатор зв’язку та дозволяє автоматично
видаляти дані через `cascade="all, delete-orphan"`, де це визначено моделлю.

### 5.2 Переліки

Файл `app/core/enums.py` містить типізовані статуси та категорії:

- студент: `ACTIVE`, `ACADEMIC_LEAVE`, `EXPELLED`, `GRADUATED`;
- форма навчання;
- відвідуваність;
- тип контролю;
- шкала оцінювання;
- чергування;
- завдання;
- події;
- зустрічі;
- журнал кураторської роботи;
- нотатки;
- аудит;
- періоди;
- сповіщення;
- хронологія;
- імпорт;
- ролі користувача.

## 6. Автентифікація й паролі

Сервіс `c.auth` підтримує реєстрацію, вхід, вихід, поточного користувача,
зміну пароля.

Паролі хешуються алгоритмом PBKDF2-SHA256 із випадковою salt і
120 000 ітерацій:

```python
def hash_password(password: str) -> str:
    if not password or len(password) < 6:
        raise ValueError("password must be at least 6 characters")
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        120_000,
    ).hex()
    return f"pbkdf2_sha256$120000${salt}${digest}"
```

Перевірка пароля не розкриває його зміст і порівнює hash через
`hmac.compare_digest`.

Вхід:

```python
def login(self, data):
    payload = parse_schema(LoginRequest, data)
    user = self.repo.get_by_username(payload.username.strip().lower())
    if user is None or not user.is_active or user.is_archived:
        raise AuthError("invalid username or password")
    if not verify_password(payload.password, user.password_hash):
        raise AuthError("invalid username or password")
    self._set_session(user)
    return AuthSessionOut(
        user=UserOut.model_validate(user),
        message="logged_in",
    )
```

Сесія користувача зберігається у налаштуваннях через ключ
`auth.current_user_id`.

## 7. Основні CRM-сервіси

### 7.1 Академічні групи

`c.groups`:

- `create(data)` — створити групу;
- `update(group_id, data)` — оновити;
- `get(group_id)` — отримати;
- `list(filters)` — пошук з пагінацією;
- `archive(group_id)` — архівувати;
- `restore(group_id)` — відновити;
- `count(include_archived)` — підрахунок.

### 7.2 Студенти

`c.students`:

- `create`, `update`, `get`, `list`;
- `archive`, `restore`;
- `summary(student_id)`.

Створення перевіряє майбутню дату народження, існування групи та унікальний
номер студента.

```python
def create(self, data):
    payload = self._parse(StudentCreate, data)
    if payload.birth_date:
        ensure_not_future(payload.birth_date, "birth_date")
    self.groups.get_or_raise(payload.group_id, "Group")
    if self.repo.get_by_number(payload.student_number):
        raise ConflictError(
            f"student_number already exists: {payload.student_number}"
        )
    student = Student(**payload.model_dump())
    self.repo.add(student)
    self.audit(
        student.id,
        AuditOperation.CREATE,
        {"student_number": student.student_number},
    )
    self.commit()
    return self._to_out(student)
```

`summary` повертає кількість пропусків, уважених пропусків, відкритих
завдань, подій і зустрічей.

### 7.3 Навчальні предмети й академічні записи

`c.academic` підтримує:

- створення, оновлення та перелік предметів;
- створення й оновлення академічних записів;
- пошук записів із фільтрами;
- середній бал конкретного студента.

Академічний запис може містити числовий бал або текстовий результат.

### 7.4 Відвідуваність

`c.attendance`:

- створення заняття;
- отримання заняття;
- позначення відвідуваності одного студента;
- масове позначення;
- оновлення запису;
- фільтрований список;
- статистика пропусків студента;
- ТОП відсутніх.

Маскова позначка реалізована upsert: для існуючого запису оновлюється статус,
для нового — створюється новий запис.

### 7.5 Чергування

`c.duties` підтримує CRUD-подібні методи, фільтрацію й перевірку перетину
чергувань за студентами.

### 7.6 Завдання

`c.assignments`:

- create/update/get/list;
- `complete` — завершити завдання;
- `overdue` — знайти прострочені завдання.

Status і effective status можуть розділяти фактичний статус і похідний стан
простроченості.

### 7.7 Події

`c.events` підтримує:

- створення й оновлення;
- скасування;
- пошук і пагінацію;
- зв’язки студентів-відповідальних;
- попередження про перетин часу;
- перевірку допустимих переходів статусу.

### 7.8 Зустрічі

`c.meetings` підтримує:

- створення й оновлення;
- завершення;
- скасування;
- пошук;
- прив’язку студентів.

### 7.9 Кураторський журнал

`c.curator_logs` підтримує створення, оновлення, отримання й пошук записів.
Запис прив’язується до кількох студентів і містить категорію, дату,
заголовок та опис.

### 7.10 Нотатки

`c.notes` підтримує створення, редагування, закріплення, архівування й фільтрацію.
Нотатка прив’язана до студента.

## 8. Пошук

`c.search.search(query)` виконує глобальний пошук у сутностях проєкту.
Вхід і відповіді описані схемами `GlobalSearchQuery` та `GlobalSearchResult`.

Пошук передбачено інтегрувати в єдине поле GUI замість окремих запитів до
SQL або окремих пошукових форм кожного сервісу.

## 9. Календар і розклад

`c.calendar` об’єднує події, зустрічі, чергування й прострочені завдання
в єдину часову стрічку.

Методи:

- `for_period`;
- `for_day`;
- `for_week`;
- `for_month`;
- `upcoming`;
- `without_responsible`;
- `find_conflicts`;
- `get_agenda`;
- `reschedule_event`;
- `create_recurring_events`.

Пошук конфліктів порівнює час початку та завершення і повертає лівий і правий
об’єкти, що перетинаються:

```python
if a["starts_at"] < b["ends_at"] and b["starts_at"] < a["ends_at"]:
    conflicts.append({
        "left": a,
        "right": b,
        "message": (
            f"{a['kind']}#{a['id']} overlaps "
            f"{b['kind']}#{b['id']}"
        ),
    })
```

Повторювані події створюються через `dateutil.rrule` у вигляді окремих записів
`Event` із спільним `recurrence_group_id`.

## 10. Хронологія студента

`c.timeline.get_timeline(...)` збирає єдину сторінку подій студента без окремої
таблиці хронології.

Підтримувані типи:

- відвідуваність;
- академічні записи;
- завдання;
- чергування;
- події;
- зустрічі;
- записи кураторського журналу;
- нотатки.

Результати сортуються за часом у зворотному порядку, після чого застосовуються
`limit` і `offset`.

```python
items.sort(key=lambda x: x.occurred_at, reverse=True)
total = len(items)
page = items[offset:offset + limit]
return PageResult(items=page, total=total, offset=offset, limit=limit)
```

Можна передати конкретний навчальний період, і метод самостійно застосує його
дати до фільтрації.

## 11. Статистика

`c.statistics` формує об’єктивні числові показники без суб’єктивних міток:

- загальна кількість студентів;
- активні й архівовані студенти;
- пропуски та поважні пропуски;
- заплановані й завершені події;
- виконані й прострочені завдання;
- загальна кількість чергувань;
- зустрічі;
- записи кураторського журналу;
- динаміка відвідуваності;
- порівняння двох періодів;
- прострочені завдання;
- підсумок активності.

Приклад:

```python
trend = c.statistics.get_attendance_trend(
    granularity="week",
    date_from=date(2026, 9, 1),
    date_to=date(2026, 12, 31),
)

comparison = c.statistics.compare_periods(
    {"date_from": "2026-09-01", "date_to": "2026-12-31"},
    {"date_from": "2025-09-01", "date_to": "2025-12-31"},
)
```

Динаміка відвідуваності групується за місяцем або ISO-тижнем і підраховує
`present`, `absent`, `excused`, `late`.

## 12. Масові операції

`c.bulk` дає preview і atomic/bulk-операції.

Підтримувані сценарії:

- масове позначення відвідуваності групи;
- масове оновлення завдань;
- пакетне планування чергувань;
- додавання учасників події;
- масове архівування студентів.

Головний принцип: методи приймають `preview=True` і спочатку повертають
опис майбутніх змін без запису в БД.

```python
def preview_group_attendance(
    lesson_id,
    group_id,
    default_status=AttendanceStatus.PRESENT,
):
    return self.mark_group_attendance({
        "lesson_id": lesson_id,
        "group_id": group_id,
        "default_status": default_status,
        "preview": True,
    })
```

У разі помилки масові методи роблять rollback і повертають
`BulkResult` із полями помилок, попереджень або деталей змін.

## 13. Імпорт студентів

`c.imports` підтримує CSV/XLSX:

- preview;
- validation;
- execute;
- отримання звіту.

Процес складається із трьох кроків:

1. `preview_import(path, mapping, group_id)` — читає файл і створює `ImportJob`.
2. `validate_import(job_id)` — перевіряє, чи немає помилок.
3. `execute_import(job_id)` — створює нових студентів.

Імпорт перевіряє обов’язкові поля, дублікати номерів всередині файлу,
існування номера в БД і можливі співпадіння ПІБ.

Особливість: існуючий студент з тим самим номером пропускається.
ПІБ не перезаписується. Файлова дублікатна ПІБ-ситуація створює попередження,
але може створити новий запис із унікальним номером.

## 14. Сповіщення й нагадування

`c.notifications`:

- отримати активні сповіщення;
- позначити прочитаним;
- відкласти;
- скасувати;
- створити або оновити notification;
- idempotent-згенерувати нагадування;
- підрахувати активні.

`c.reminders.generate()` створює нагадування про події, зустрічі,
чергування, завдання та пропущене позначення відвідуваності.

Логіка snooze:

```python
def snooze(self, notification_id: int, until: datetime):
    if until <= utc_now():
        raise ValidationError("snooze until must be in the future")
    notification = self._get(notification_id)
    notification.status = NotificationStatus.SNOOZED
    notification.snoozed_until = until
    self.commit()
    return NotificationOut.model_validate(notification)
```

Повторна генерація не створює дублікати завдяки upsert за парою
`kind + source_type + source_id`.

## 15. Навчальні періоди

`c.periods` підтримує:

- створення й оновлення періодів;
- встановлення поточного періоду;
- list/get/archive;
- розв’язання дат із явними `date_from/date_to`.

Академічний період може типізовано позначати семестр або навчальний рік.
Календар, timeline і статистика можуть використовувати `period_id`.

## 16. Експорт і звіти

`c.reports` створює CSV, XLSX або PDF-файли в каталозі exports.

Підтримувані звіти:

- студенти;
- відвідуваність;
- завдання;
- чергування;
- події;
- кураторський журнал;
- узагальнена статистика.

Приклад:

```python
result = c.reports.export_students("xlsx", group_id=1)
print(result.path)
print(result.rows)
```

CSV/XLSX/PDF реалізовані в модулі `app/readers/import_export.py`.

## 17. Backup і відновлення

`c.backup` використовує native SQLite backup API:

- `create_backup(label)`;
- `restore(backup_path, make_safety_backup=True)`;
- `verify_integrity(db_path)`;
- `list_backups()`.

Ключова реалізація:

```python
with sqlite3.connect(self.database_path) as src:
    with sqlite3.connect(dest) as dst:
        src.backup(dst)
```

Перед відновленням перевіряється цілісність backup-файлу.
За замовчуванням створюється резервна копія поточної БД з міткою
`pre_restore`.

## 18. Аудит

Сервіс `c.audit` дозволяє:

- переглянути записи конкретної сутності;
- переглянути останні записи;
- показати diff змін.

Будь-яка створена сутність може отримати audit-запис із типом операції,
старими/новими значеннями та оператором.

Типові операції:

- CREATE;
- UPDATE;
- DELETE;
- ARCHIVE;
- RESTORE;
- STATUS_CHANGE;
- LOGIN;
- LOGOUT;
- EXPORT;
- IMPORT.

## 19. Перевірка цілісності даних

`c.integrity.run_checks()` виконує read-only перевірки:

- дублікати номерів студентів;
- orphaned many-to-many-зв’язки;
- відвідуваність із відсутнім заняттям;
- події з датою завершення раніше початку;
- активні студенти в архівованій групі;
- порожні обов’язкові поля.

Результат містить `ok` і список структурованих `IntegrityIssue`.

## 20. Налаштування

`c.settings` дає доступ до пар key/value:

- `get`;
- `set`;
- `all`;
- інтервали нагадувань;
- налаштування за замовчуванням.

Налаштування нагадувань описані Pydantic-моделлю і зберігаються в
`AppSetting`.

## 21. База даних і міграції

SQLite engine налаштований у `app/database/engine.py`, а підключення —
у `app/database/session.py`.

При ініціалізації:

```python
def init_database(engine=None, *, create_schema=True):
    import app.models
    if engine is None:
        engine = get_engine()
    else:
        set_engine(engine)

    configure_session_factory(engine)
    if create_schema:
        Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))
        rows = conn.execute(text("PRAGMA foreign_key_check")).fetchall()
        if rows:
            raise RuntimeError("Foreign key check failed")
        conn.commit()
    return engine
```

Включені перевірки foreign key і перевірка на orphan references.
У каталозі `alembic/versions/` є baseline-міграції:

- `001_initial_schema.py`;
- `002_v2_extensions.py`;
- `003_users_auth.py`.

## 22. Повний інвентар публічних методів сервісів

| Сервіс | Container attr | Основні методи |
|---|---|---|
| AuthService | `auth` | register, login, logout, current_user, require_user, change_password |
| GroupService | `groups` | create, update, get, list, archive, restore, count |
| StudentService | `students` | create, update, get, list, archive, restore, summary |
| AcademicService | `academic` | create_subject, update_subject, list_subjects, create_record, update_record, list_records, average_for_student |
| AttendanceService | `attendance` | create_lesson, get_lesson, mark, bulk_mark, update, list, student_stats, top_absentees |
| DutyService | `duties` | create, update, get, list |
| AssignmentService | `assignments` | create, update, complete, get, list, overdue |
| EventService | `events` | create, update, cancel, get, list |
| MeetingService | `meetings` | create, update, complete, cancel, get, list |
| CuratorLogService | `curator_logs` | create, update, get, list |
| NoteService | `notes` | create, update, pin, archive, list |
| SearchService | `search` | search |
| CalendarService | `calendar` | for_period, for_day, for_week, for_month, upcoming, without_responsible, find_conflicts, get_agenda, reschedule_event, create_recurring_events |
| StatisticsService | `statistics` | overview, get_attendance_trend, compare_periods, get_overdue_summary, get_activity_summary |
| ReportService | `reports` | export_students, export_attendance, export_assignments, export_duties, export_events, export_curator_log, export_summary |
| AuditService | `audit` | for_entity, recent, diff_view |
| BackupService | `backup` | create_backup, restore, verify_integrity, list_backups |
| StudentTimelineService | `timeline` | get_timeline |
| PeriodService | `periods` | create, update, set_current, list, get, archive, resolve_dates |
| IntegrityService | `integrity` | run_checks |
| NotificationService | `notifications` | get_pending, mark_as_read, snooze, dismiss, upsert, generate_due_notifications, count_pending |
| ReminderService | `reminders` | generate |
| BulkOperationService | `bulk` | preview_group_attendance, mark_group_attendance, bulk_update_assignments, schedule_duties, add_event_participants, bulk_archive_students |
| ImportService | `imports` | preview_import, validate_import, execute_import, get_import_report |
| SettingsService | `settings` | get, set, get_reminder_settings, set_reminder_settings, all |

## 23. Приклад повного сценарію GUI

```python
from app.container import create_container

c = create_container()

try:
    c.auth.login({
        "username": "curator",
        "password": "curator123",
    })

    group_page = c.groups.list({"offset": 0, "limit": 50})
    student_page = c.students.list({
        "group_id": group_page.items[0].id,
        "offset": 0,
        "limit": 100,
    })

    overview = c.statistics.overview()
    agenda = c.calendar.get_agenda("week")
    pending = c.notifications.get_pending()
    integrity = c.integrity.run_checks()

    print(group_page)
    print(student_page)
    print(overview)
    print(agenda)
    print(pending)
    print(integrity)
finally:
    c.close()
```

## 24. Тестування

У проєкті є модульні й інтеграційні pytest-тести для:

- автентифікації;
- бази даних і seed;
- груп;
- студентів;
- академічних записів;
- відвідуваності;
- завдань;
- чергувань;
- подій і повторювань;
- зустрічей;
- журналу;
- пошуку;
- backup;
- аудитологу;
- bulk-операцій;
- імпорту;
- сповіщень;
- timeline;
- календаря;
- статистики;
- звітів;
- перевірки цілісності.

Команди:

```powershell
pytest -q
pytest --cov=app --cov-report=term-missing
```
