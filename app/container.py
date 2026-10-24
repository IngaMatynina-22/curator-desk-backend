"""Service container — single entry point for GUI / scripts."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.initialization import init_database
from app.database.session import get_session
from app.services.academic_service import AcademicService
from app.services.assignment_service import AssignmentService
from app.services.attendance_service import AttendanceService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.backup_service import BackupService
from app.services.bulk_operation_service import BulkOperationService
from app.services.calendar_service import CalendarService
from app.services.curator_log_service import CuratorLogService
from app.services.duty_service import DutyService
from app.services.event_service import EventService
from app.services.group_service import GroupService
from app.services.import_service import ImportService
from app.services.integrity_service import IntegrityService
from app.services.meeting_service import MeetingService
from app.services.note_service import NoteService
from app.services.notification_service import NotificationService
from app.services.period_service import PeriodService
from app.services.reminder_service import ReminderService
from app.services.report_service import ReportService
from app.services.search_service import SearchService
from app.services.settings_service import SettingsService
from app.services.statistics_service import StatisticsService
from app.services.student_service import StudentService
from app.services.student_timeline_service import StudentTimelineService


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
        # v2
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
