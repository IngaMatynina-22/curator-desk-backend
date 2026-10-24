"""Test data factories."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from app.container import ServiceContainer
from app.core.date_utils import utc_now


def make_group(container: ServiceContainer, name: str = "КН-21", **kwargs):
    data = {
        "name": name,
        "specialty": "Computer Science",
        "course": 3,
        "academic_year": "2025/2026",
        "curator_name": "curator",
        **kwargs,
    }
    return container.groups.create(data)


def make_student(container: ServiceContainer, group_id: int, number: str = "KN-01", **kwargs):
    data = {
        "student_number": number,
        "last_name": "Testov",
        "first_name": "Ivan",
        "group_id": group_id,
        **kwargs,
    }
    return container.students.create(data)


def make_subject(container: ServiceContainer, name: str = "Databases", **kwargs):
    return container.academic.create_subject({"name": name, **kwargs})


def make_lesson(container: ServiceContainer, subject_id: int, **kwargs):
    data = {
        "lesson_date": date.today(),
        "subject_id": subject_id,
        "pair_number": 1,
        **kwargs,
    }
    return container.attendance.create_lesson(data)


def seed_basic(container: ServiceContainer):
    group = make_group(container)
    s1 = make_student(container, group.id, "KN-01", last_name="Ivanov", first_name="Oleh")
    s2 = make_student(container, group.id, "KN-02", last_name="Petrenko", first_name="Anna")
    subject = make_subject(container)
    return group, s1, s2, subject
