"""Shared enumerations / allowed value sets."""

from enum import StrEnum


class StudentStatus(StrEnum):
    ACTIVE = "active"
    ACADEMIC_LEAVE = "academic_leave"
    EXPELLED = "expelled"
    TRANSFERRED = "transferred"
    GRADUATED = "graduated"


class StudyForm(StrEnum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    DISTANCE = "distance"


class AttendanceStatus(StrEnum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


class ControlType(StrEnum):
    EXAM = "exam"
    CREDIT = "credit"
    TEST = "test"
    COURSEWORK = "coursework"
    OTHER = "other"


class GradeScale(StrEnum):
    NUMERIC = "numeric"
    CREDIT_PASS = "credit_pass"
    TEXT = "text"


class DutyStatus(StrEnum):
    PLANNED = "planned"
    DONE = "done"
    NOT_DONE = "not_done"
    CANCELLED = "cancelled"


class AssignmentStatus(StrEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class AssignmentPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EventStatus(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EventType(StrEnum):
    GROUP_MEETING = "group_meeting"
    CULTURAL = "cultural"
    ORGANIZATIONAL = "organizational"
    EDUCATIONAL = "educational"
    OTHER = "other"


class MeetingFormat(StrEnum):
    INDIVIDUAL = "individual"
    GROUP = "group"


class MeetingStatus(StrEnum):
    PLANNED = "planned"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class CuratorLogCategory(StrEnum):
    ORGANIZATIONAL = "organizational"
    STUDENT_COMMUNICATION = "student_communication"
    TEACHER_INTERACTION = "teacher_interaction"
    PARENT_INTERACTION = "parent_interaction"
    ACADEMIC = "academic"
    EDUCATIONAL_EVENT = "educational_event"
    PREVENTIVE = "preventive"
    OTHER = "other"


class NoteCategory(StrEnum):
    GENERAL = "general"
    IMPORTANT = "important"
    FOLLOW_UP = "follow_up"
    OTHER = "other"


class AuditOperation(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    ARCHIVE = "archive"
    RESTORE = "restore"


class EventStudentRole(StrEnum):
    PARTICIPANT = "participant"
    RESPONSIBLE = "responsible"


class PeriodKind(StrEnum):
    SEMESTER = "semester"
    YEAR = "year"


class NotificationKind(StrEnum):
    EVENT_UPCOMING = "event_upcoming"
    MEETING_UPCOMING = "meeting_upcoming"
    DUTY_UPCOMING = "duty_upcoming"
    ASSIGNMENT_DUE = "assignment_due"
    ASSIGNMENT_OVERDUE = "assignment_overdue"
    ATTENDANCE_MISSING = "attendance_missing"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    READ = "read"
    SNOOZED = "snoozed"
    DISMISSED = "dismissed"


class TimelineKind(StrEnum):
    ATTENDANCE = "attendance"
    ACADEMIC = "academic"
    ASSIGNMENT = "assignment"
    DUTY = "duty"
    EVENT = "event"
    MEETING = "meeting"
    CURATOR_LOG = "curator_log"
    NOTE = "note"


class ImportJobStatus(StrEnum):
    PREVIEW = "preview"
    VALIDATED = "validated"
    COMPLETED = "completed"
    FAILED = "failed"


class UserRole(StrEnum):
    CURATOR = "curator"
    ADMIN = "admin"
