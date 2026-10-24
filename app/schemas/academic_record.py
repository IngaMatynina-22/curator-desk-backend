from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.core.enums import ControlType, GradeScale
from app.schemas.common import ORMModel


class SubjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str | None = None
    description: str | None = None


class SubjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    code: str | None = None
    description: str | None = None


class SubjectOut(ORMModel):
    id: int
    name: str
    code: str | None
    description: str | None
    is_archived: bool


class AcademicRecordCreate(BaseModel):
    student_id: int
    subject_id: int
    record_date: date
    control_type: ControlType = ControlType.OTHER
    grade_scale: GradeScale = GradeScale.NUMERIC
    score: float | None = None
    max_score: float | None = None
    text_result: str | None = None
    comment: str | None = None

    @model_validator(mode="after")
    def validate_result(self) -> "AcademicRecordCreate":
        if self.grade_scale == GradeScale.NUMERIC and self.score is None:
            raise ValueError("score is required for numeric scale")
        if self.grade_scale == GradeScale.CREDIT_PASS and not self.text_result:
            raise ValueError("text_result is required for credit_pass scale")
        if self.max_score is not None and self.score is not None and self.score > self.max_score:
            raise ValueError("score cannot exceed max_score")
        return self


class AcademicRecordUpdate(BaseModel):
    record_date: date | None = None
    control_type: ControlType | None = None
    grade_scale: GradeScale | None = None
    score: float | None = None
    max_score: float | None = None
    text_result: str | None = None
    comment: str | None = None


class AcademicRecordFilter(BaseModel):
    student_id: int | None = None
    subject_id: int | None = None
    grade_scale: GradeScale | None = None
    date_from: date | None = None
    date_to: date | None = None
    offset: int = 0
    limit: int = 50


class AcademicRecordOut(ORMModel):
    id: int
    student_id: int
    subject_id: int
    record_date: date
    control_type: str
    grade_scale: str
    score: float | None
    max_score: float | None
    text_result: str | None
    comment: str | None
    created_at: datetime
    updated_at: datetime
