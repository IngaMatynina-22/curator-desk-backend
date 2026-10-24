from datetime import date

from app.core.enums import GradeScale
from app.core.exceptions import ValidationError
from tests.factories import seed_basic


def test_academic_records_and_average(container):
    _, student, _, subject = seed_basic(container)
    container.academic.create_record(
        {
            "student_id": student.id,
            "subject_id": subject.id,
            "record_date": date.today(),
            "grade_scale": GradeScale.NUMERIC,
            "score": 90,
            "max_score": 100,
        }
    )
    container.academic.create_record(
        {
            "student_id": student.id,
            "subject_id": subject.id,
            "record_date": date.today(),
            "grade_scale": GradeScale.NUMERIC,
            "score": 80,
            "max_score": 100,
        }
    )
    avg = container.academic.average_for_student(student.id)
    assert avg == 85.0

    listed = container.academic.list_records({"student_id": student.id})
    assert listed.total == 2


def test_credit_requires_text(container):
    _, student, _, subject = seed_basic(container)
    try:
        container.academic.create_record(
            {
                "student_id": student.id,
                "subject_id": subject.id,
                "record_date": date.today(),
                "grade_scale": GradeScale.CREDIT_PASS,
            }
        )
        assert False
    except ValidationError:
        pass
