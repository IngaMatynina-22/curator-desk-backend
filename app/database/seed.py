"""Full demo seed for CuratorDesk."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import (
    AssignmentPriority,
    AssignmentStatus,
    AttendanceStatus,
    ControlType,
    CuratorLogCategory,
    DutyStatus,
    EventStatus,
    EventStudentRole,
    EventType,
    GradeScale,
    MeetingFormat,
    MeetingStatus,
    NoteCategory,
    PeriodKind,
    StudentStatus,
    StudyForm,
    UserRole,
)
from app.core.security import hash_password
from app.models.academic_group import AcademicGroup
from app.models.academic_period import AcademicPeriod
from app.models.academic_record import AcademicRecord
from app.models.assignment import Assignment
from app.models.associations import (
    AssignmentStudent,
    CuratorLogStudent,
    DutyStudent,
    EventStudent,
    MeetingStudent,
)
from app.models.attendance import AttendanceRecord, Lesson
from app.models.curator_log import CuratorLog
from app.models.duty import Duty
from app.models.event import Event
from app.models.meeting import Meeting
from app.models.note import Note
from app.models.student import Student
from app.models.subject import Subject
from app.models.user import User

DEMO_USERNAME = "curator"
DEMO_PASSWORD = "curator123"


def is_seeded(session: Session) -> bool:
    users = session.scalar(select(func.count()).select_from(User)) or 0
    groups = session.scalar(select(func.count()).select_from(AcademicGroup)) or 0
    return users > 0 or groups > 0


def seed_full(session: Session, *, force: bool = False) -> dict:
    """Populate demo curator account and rich academic group data."""
    if is_seeded(session) and not force:
        return {"skipped": True, "reason": "database already has data"}

    today = date.today()
    now = datetime.now().replace(microsecond=0)

    user = User(
        username=DEMO_USERNAME,
        email="curator@curatordesk.local",
        full_name="Демо Куратор",
        password_hash=hash_password(DEMO_PASSWORD),
        role=UserRole.CURATOR,
        is_active=True,
    )
    session.add(user)

    period = AcademicPeriod(
        name="Осінній семестр 2025/2026",
        academic_year="2025/2026",
        kind=PeriodKind.SEMESTER,
        starts_on=date(2025, 9, 1),
        ends_on=date(2026, 1, 31),
        is_current=True,
    )
    session.add(period)

    group = AcademicGroup(
        name="КН-21",
        specialty="Комп'ютерні науки",
        course=3,
        academic_year="2025/2026",
        curator_name="Демо Куратор",
    )
    session.add(group)
    session.flush()

    student_specs = [
        ("KN-2101", "Іваненко", "Олена", "Петрівна"),
        ("KN-2102", "Петренко", "Андрій", "Ігорович"),
        ("KN-2103", "Коваленко", "Марія", "Сергіївна"),
        ("KN-2104", "Сидоренко", "Олег", None),
        ("KN-2105", "Бондар", "Наталія", "Олександрівна"),
        ("KN-2106", "Мельник", "Дмитро", "Васильович"),
    ]
    students: list[Student] = []
    for number, last, first, middle in student_specs:
        students.append(
            Student(
                student_number=number,
                last_name=last,
                first_name=first,
                middle_name=middle,
                group_id=group.id,
                status=StudentStatus.ACTIVE,
                study_form=StudyForm.FULL_TIME,
                course=3,
                specialty=group.specialty,
                enrollment_date=date(2023, 9, 1),
                email=f"{number.lower()}@uni.local",
                phone="+380501000000",
            )
        )
    session.add_all(students)

    subjects = [
        Subject(name="Бази даних", code="DB"),
        Subject(name="Програмування", code="PROG"),
        Subject(name="Операційні системи", code="OS"),
    ]
    session.add_all(subjects)
    session.flush()

    # Academic records
    session.add_all(
        [
            AcademicRecord(
                student_id=students[0].id,
                subject_id=subjects[0].id,
                record_date=today - timedelta(days=20),
                control_type=ControlType.TEST,
                grade_scale=GradeScale.NUMERIC,
                score=90,
                max_score=100,
            ),
            AcademicRecord(
                student_id=students[1].id,
                subject_id=subjects[1].id,
                record_date=today - timedelta(days=15),
                control_type=ControlType.CREDIT,
                grade_scale=GradeScale.CREDIT_PASS,
                text_result="залік",
            ),
            AcademicRecord(
                student_id=students[2].id,
                subject_id=subjects[0].id,
                record_date=today - timedelta(days=10),
                control_type=ControlType.EXAM,
                grade_scale=GradeScale.NUMERIC,
                score=75,
                max_score=100,
                comment="Потрібна додаткова робота",
            ),
        ]
    )

    # Lessons + attendance
    lessons = [
        Lesson(lesson_date=today - timedelta(days=2), subject_id=subjects[0].id, pair_number=1, topic="SQL JOIN"),
        Lesson(lesson_date=today - timedelta(days=1), subject_id=subjects[1].id, pair_number=2, topic="OOP"),
        Lesson(lesson_date=today, subject_id=subjects[2].id, pair_number=1, topic="Processes"),
    ]
    session.add_all(lessons)
    session.flush()

    statuses = [
        AttendanceStatus.PRESENT,
        AttendanceStatus.ABSENT,
        AttendanceStatus.LATE,
        AttendanceStatus.EXCUSED,
        AttendanceStatus.PRESENT,
        AttendanceStatus.PRESENT,
    ]
    for lesson in lessons[:2]:
        for student, status in zip(students, statuses):
            hours = 2.0 if status in {AttendanceStatus.ABSENT, AttendanceStatus.EXCUSED} else 0.0
            session.add(
                AttendanceRecord(
                    lesson_id=lesson.id,
                    student_id=student.id,
                    status=status,
                    hours_missed=hours,
                    recorded_at=now,
                )
            )

    # Duties
    duty = Duty(
        duty_date=today + timedelta(days=1),
        start_time=time(9, 0),
        end_time=time(11, 0),
        location="Ауд. 301",
        duty_type="classroom",
        status=DutyStatus.PLANNED,
    )
    duty.student_links = [
        DutyStudent(student_id=students[0].id),
        DutyStudent(student_id=students[1].id),
    ]
    session.add(duty)

    # Assignments
    a1 = Assignment(
        title="Підготувати презентацію групи",
        description="5–7 слайдів про кураторську діяльність",
        due_date=today + timedelta(days=3),
        priority=AssignmentPriority.HIGH,
        status=AssignmentStatus.IN_PROGRESS,
        author=DEMO_USERNAME,
    )
    a1.student_links = [AssignmentStudent(student_id=students[0].id), AssignmentStudent(student_id=students[2].id)]
    a2 = Assignment(
        title="Зібрати контакти батьків",
        due_date=today - timedelta(days=2),
        priority=AssignmentPriority.MEDIUM,
        status=AssignmentStatus.NEW,
        author=DEMO_USERNAME,
    )
    a2.student_links = [AssignmentStudent(student_id=students[3].id)]
    session.add_all([a1, a2])

    # Events
    event = Event(
        title="Збори групи",
        description="Організаційні питання семестру",
        event_type=EventType.GROUP_MEETING,
        location="Ауд. 101",
        starts_at=now + timedelta(days=2, hours=2),
        ends_at=now + timedelta(days=2, hours=3),
        status=EventStatus.PLANNED,
    )
    event.student_links = [
        EventStudent(student_id=students[0].id, role=EventStudentRole.RESPONSIBLE),
        *[EventStudent(student_id=s.id, role=EventStudentRole.PARTICIPANT) for s in students],
    ]
    session.add(event)

    # Meetings
    meeting = Meeting(
        scheduled_at=now - timedelta(days=1),
        format=MeetingFormat.INDIVIDUAL,
        topic="Пропуски занять",
        result_summary="Домовились про відпрацювання",
        next_steps="Перевірити довідку",
        status=MeetingStatus.COMPLETED,
    )
    meeting.student_links = [MeetingStudent(student_id=students[1].id)]
    session.add(meeting)
    session.flush()

    # Curator log
    log = CuratorLog(
        occurred_at=now - timedelta(days=1),
        category=CuratorLogCategory.STUDENT_COMMUNICATION,
        title="Індивідуальна бесіда",
        description="Обговорено причини пропусків і план надолуження.",
        result="Студент погодився надати довідку",
        next_actions="Контроль через тиждень",
        meeting_id=meeting.id,
    )
    log.student_links = [CuratorLogStudent(student_id=students[1].id)]
    session.add(log)

    session.add_all(
        [
            Note(
                title="Важливо: батьківські збори",
                body="Запланувати на кінець місяця.",
                category=NoteCategory.IMPORTANT,
                is_pinned=True,
                group_id=group.id,
            ),
            Note(
                title="Контакт старости",
                body=f"Староста: {students[0].full_name}",
                category=NoteCategory.GENERAL,
                student_id=students[0].id,
            ),
        ]
    )

    session.commit()
    return {
        "skipped": False,
        "user": DEMO_USERNAME,
        "password": DEMO_PASSWORD,
        "group": group.name,
        "students": len(students),
        "subjects": len(subjects),
        "period": period.name,
    }


# backward-compatible alias
def seed_demo(session: Session) -> AcademicGroup:
    result = seed_full(session)
    group = session.scalar(select(AcademicGroup).order_by(AcademicGroup.id))
    if group is None:
        raise RuntimeError(f"seed failed: {result}")
    return group
