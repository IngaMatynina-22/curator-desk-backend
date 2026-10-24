from __future__ import annotations

from sqlalchemy import func, select

from app.core.enums import AttendanceStatus
from app.models.attendance import AttendanceRecord, Lesson
from app.repositories.base import BaseRepository
from app.schemas.attendance import AttendanceFilter


class LessonRepository(BaseRepository[Lesson]):
    model = Lesson


class AttendanceRepository(BaseRepository[AttendanceRecord]):
    model = AttendanceRecord

    def get_for_lesson_student(self, lesson_id: int, student_id: int) -> AttendanceRecord | None:
        return self.session.scalar(
            select(AttendanceRecord).where(
                AttendanceRecord.lesson_id == lesson_id,
                AttendanceRecord.student_id == student_id,
            )
        )

    def search(self, filters: AttendanceFilter) -> tuple[list[AttendanceRecord], int]:
        stmt = select(AttendanceRecord).join(Lesson)
        if filters.student_id is not None:
            stmt = stmt.where(AttendanceRecord.student_id == filters.student_id)
        if filters.subject_id is not None:
            stmt = stmt.where(Lesson.subject_id == filters.subject_id)
        if filters.status is not None:
            stmt = stmt.where(AttendanceRecord.status == filters.status)
        if filters.date_from is not None:
            stmt = stmt.where(Lesson.lesson_date >= filters.date_from)
        if filters.date_to is not None:
            stmt = stmt.where(Lesson.lesson_date <= filters.date_to)
        stmt = stmt.order_by(Lesson.lesson_date.desc())
        return self.paginate(stmt, offset=filters.offset, limit=filters.limit)

    def absence_stats(self, student_id: int, date_from=None, date_to=None) -> dict:
        stmt = (
            select(
                AttendanceRecord.status,
                func.count(),
                func.coalesce(func.sum(AttendanceRecord.hours_missed), 0.0),
            )
            .join(Lesson)
            .where(AttendanceRecord.student_id == student_id)
            .group_by(AttendanceRecord.status)
        )
        if date_from is not None:
            stmt = stmt.where(Lesson.lesson_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(Lesson.lesson_date <= date_to)

        stats = {
            "student_id": student_id,
            "absences": 0,
            "excused": 0,
            "late": 0,
            "hours_missed": 0.0,
        }
        for status, count, hours in self.session.execute(stmt):
            if status == AttendanceStatus.ABSENT:
                stats["absences"] = int(count)
            elif status == AttendanceStatus.EXCUSED:
                stats["excused"] = int(count)
            elif status == AttendanceStatus.LATE:
                stats["late"] = int(count)
            if status in {
                AttendanceStatus.ABSENT,
                AttendanceStatus.EXCUSED,
                AttendanceStatus.LATE,
            }:
                stats["hours_missed"] += float(hours or 0)
        return stats

    def top_absentees(self, limit: int = 10, date_from=None, date_to=None) -> list[tuple[int, int]]:
        stmt = (
            select(AttendanceRecord.student_id, func.count())
            .join(Lesson)
            .where(
                AttendanceRecord.status.in_(
                    [AttendanceStatus.ABSENT, AttendanceStatus.EXCUSED]
                )
            )
            .group_by(AttendanceRecord.student_id)
            .order_by(func.count().desc())
            .limit(limit)
        )
        if date_from is not None:
            stmt = stmt.where(Lesson.lesson_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(Lesson.lesson_date <= date_to)
        return [(int(sid), int(cnt)) for sid, cnt in self.session.execute(stmt)]
