"""ORM models package — importing populates metadata."""

from app.models.academic_group import AcademicGroup
from app.models.academic_period import AcademicPeriod
from app.models.academic_record import AcademicRecord
from app.models.app_setting import AppSetting
from app.models.assignment import Assignment
from app.models.associations import (
    AssignmentStudent,
    CuratorLogStudent,
    DutyStudent,
    EventStudent,
    MeetingStudent,
)
from app.models.attachment import Attachment
from app.models.attendance import AttendanceRecord, Lesson
from app.models.audit_log import AuditLog
from app.models.curator_log import CuratorLog
from app.models.duty import Duty
from app.models.event import Event
from app.models.import_job import ImportJob
from app.models.meeting import Meeting
from app.models.note import Note
from app.models.notification import Notification
from app.models.student import Student
from app.models.subject import Subject
from app.models.user import User

__all__ = [
    "AcademicGroup",
    "AcademicPeriod",
    "AcademicRecord",
    "AppSetting",
    "Assignment",
    "AssignmentStudent",
    "Attachment",
    "AttendanceRecord",
    "AuditLog",
    "CuratorLog",
    "CuratorLogStudent",
    "Duty",
    "DutyStudent",
    "Event",
    "EventStudent",
    "ImportJob",
    "Lesson",
    "Meeting",
    "MeetingStudent",
    "Note",
    "Notification",
    "Student",
    "Subject",
    "User",
]
