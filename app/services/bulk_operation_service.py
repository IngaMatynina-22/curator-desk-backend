from __future__ import annotations

from datetime import time

from sqlalchemy import select

from app.core.enums import AttendanceStatus, EventStudentRole
from app.core.exceptions import ValidationError
from app.models.associations import EventStudent
from app.models.student import Student
from app.schemas.bulk import (
    BulkAssignmentUpdate,
    BulkResult,
    DutyPlanItem,
    GroupAttendanceRequest,
    ScheduleDutiesRequest,
)
from app.services.assignment_service import AssignmentService
from app.services.attendance_service import AttendanceService
from app.services.base import BaseService
from app.services.duty_service import DutyService
from app.services.event_service import EventService
from app.services.parse import parse_schema
from app.services.student_service import StudentService


class BulkOperationService(BaseService):
    def __init__(self, session):
        super().__init__(session)
        self.attendance = AttendanceService(session)
        self.assignments = AssignmentService(session)
        self.duties = DutyService(session)
        self.events = EventService(session)
        self.students = StudentService(session)

    def preview_group_attendance(
        self, lesson_id: int, group_id: int, default_status: AttendanceStatus = AttendanceStatus.PRESENT
    ) -> BulkResult:
        return self.mark_group_attendance(
            {
                "lesson_id": lesson_id,
                "group_id": group_id,
                "default_status": default_status,
                "preview": True,
            }
        )

    def mark_group_attendance(self, data: GroupAttendanceRequest | dict) -> BulkResult:
        req = parse_schema(GroupAttendanceRequest, data)
        self.attendance.lessons.get_or_raise(req.lesson_id, "Lesson")
        students = list(
            self.session.scalars(
                select(Student).where(
                    Student.group_id == req.group_id,
                    Student.is_archived.is_(False),
                )
            )
        )
        marks = [
            {"student_id": s.id, "status": req.default_status}
            for s in students
            if self.attendance.attendance.get_for_lesson_student(req.lesson_id, s.id) is None
        ]
        skipped = len(students) - len(marks)
        details = [{"student_id": m["student_id"], "status": str(m["status"])} for m in marks]
        if req.preview:
            return BulkResult(
                applied=0,
                skipped=skipped,
                preview_only=True,
                details=details,
                warnings=[] if marks else ["no students to mark"],
            )
        try:
            if marks:
                self.attendance.bulk_mark({"lesson_id": req.lesson_id, "marks": marks})
            return BulkResult(applied=len(marks), skipped=skipped, details=details)
        except Exception as exc:
            self.session.rollback()
            return BulkResult(errors=[str(exc)], skipped=len(students))

    def bulk_update_assignments(self, data: BulkAssignmentUpdate | dict) -> BulkResult:
        req = parse_schema(BulkAssignmentUpdate, data)
        patch = req.model_dump(exclude={"ids", "preview"}, exclude_none=True)
        if not patch:
            raise ValidationError("no assignment fields to update")
        details = [{"id": i, **patch} for i in req.ids]
        if req.preview:
            return BulkResult(preview_only=True, details=details, applied=0)
        try:
            for aid in req.ids:
                entity = self.assignments.repo.get_or_raise(aid, "Assignment")
                for key, value in patch.items():
                    setattr(entity, key, value)
            self.flush()
            self.commit()
            return BulkResult(applied=len(req.ids), details=details)
        except Exception as exc:
            self.session.rollback()
            return BulkResult(applied=0, errors=[str(exc)], details=details)

    def schedule_duties(self, data: ScheduleDutiesRequest | dict) -> BulkResult:
        req = parse_schema(ScheduleDutiesRequest, data)
        details = [item.model_dump() for item in req.plan]
        if req.preview:
            return BulkResult(preview_only=True, details=details)
        applied = 0
        warnings: list[str] = []
        try:
            for item in req.plan:
                payload = {
                    "duty_date": item.duty_date,
                    "student_ids": item.student_ids,
                    "location": item.location,
                    "duty_type": item.duty_type,
                }
                if item.start_time:
                    h, m = map(int, item.start_time.split(":")[:2])
                    payload["start_time"] = time(h, m)
                if item.end_time:
                    h, m = map(int, item.end_time.split(":")[:2])
                    payload["end_time"] = time(h, m)
                out = self.duties.create(payload)
                applied += 1
                warnings.extend(out.warnings)
            return BulkResult(applied=applied, warnings=warnings, details=details)
        except Exception as exc:
            self.session.rollback()
            return BulkResult(errors=[str(exc)], warnings=warnings)

    def add_event_participants(self, event_id: int, student_ids: list[int], preview: bool = False) -> BulkResult:
        event = self.events.repo.get_or_raise(event_id, "Event")
        existing = set(event.participant_ids)
        to_add = [sid for sid in student_ids if sid not in existing]
        details = [{"student_id": sid} for sid in to_add]
        if preview:
            return BulkResult(preview_only=True, details=details, skipped=len(student_ids) - len(to_add))
        try:
            self.students.repo.ensure_ids_exist(to_add, "Student")
            for sid in to_add:
                event.student_links.append(
                    EventStudent(student_id=sid, role=EventStudentRole.PARTICIPANT)
                )
            self.flush()
            self.commit()
            return BulkResult(applied=len(to_add), skipped=len(student_ids) - len(to_add), details=details)
        except Exception as exc:
            self.session.rollback()
            return BulkResult(errors=[str(exc)])

    def bulk_archive_students(self, ids: list[int], preview: bool = False) -> BulkResult:
        details = [{"student_id": i} for i in ids]
        if preview:
            return BulkResult(preview_only=True, details=details)
        try:
            for sid in ids:
                entity = self.students.repo.get_or_raise(sid, "Student")
                self.students.repo.archive(entity)
            self.flush()
            self.commit()
            return BulkResult(applied=len(ids), details=details)
        except Exception as exc:
            self.session.rollback()
            return BulkResult(errors=[str(exc)])
