from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.core.enums import StudentStatus, StudyForm
from app.schemas.common import ORMModel


class StudentCreate(BaseModel):
    student_number: str = Field(..., min_length=1, max_length=64)
    last_name: str = Field(..., min_length=1, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    middle_name: str | None = None
    birth_date: date | None = None
    phone: str | None = Field(None, max_length=32)
    email: str | None = None
    address: str | None = None
    emergency_contact: str | None = None
    personal_notes: str | None = None
    group_id: int
    enrollment_date: date | None = None
    status: StudentStatus = StudentStatus.ACTIVE
    study_form: StudyForm = StudyForm.FULL_TIME
    course: int | None = Field(None, ge=1, le=10)
    specialty: str | None = None
    academic_notes: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("invalid email format")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        digits = "".join(ch for ch in value if ch.isdigit() or ch == "+")
        if len(digits) < 7:
            raise ValueError("invalid phone format")
        return value


class StudentUpdate(BaseModel):
    student_number: str | None = Field(None, min_length=1, max_length=64)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    first_name: str | None = Field(None, min_length=1, max_length=100)
    middle_name: str | None = None
    birth_date: date | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    emergency_contact: str | None = None
    personal_notes: str | None = None
    group_id: int | None = None
    enrollment_date: date | None = None
    status: StudentStatus | None = None
    study_form: StudyForm | None = None
    course: int | None = Field(None, ge=1, le=10)
    specialty: str | None = None
    academic_notes: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("invalid email format")
        return value


class StudentFilter(BaseModel):
    query: str | None = None
    group_id: int | None = None
    status: StudentStatus | None = None
    include_archived: bool = False
    offset: int = 0
    limit: int = 50
    sort_by: str = "last_name"
    sort_dir: str = "asc"


class StudentOut(ORMModel):
    id: int
    student_number: str
    last_name: str
    first_name: str
    middle_name: str | None
    birth_date: date | None
    phone: str | None
    email: str | None
    address: str | None
    emergency_contact: str | None
    personal_notes: str | None
    group_id: int
    enrollment_date: date | None
    status: str
    study_form: str
    course: int | None
    specialty: str | None
    academic_notes: str | None
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    full_name: str | None = None


class StudentSummary(BaseModel):
    student: StudentOut
    attendance_absences: int = 0
    attendance_excused: int = 0
    open_assignments: int = 0
    events_count: int = 0
    meetings_count: int = 0
