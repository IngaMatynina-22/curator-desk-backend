from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from app.core.enums import ImportJobStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.models.import_job import ImportJob
from app.models.student import Student
from app.readers.import_export import read_tabular
from app.repositories.group_repository import GroupRepository
from app.repositories.student_repository import StudentRepository
from app.schemas.import_job import ImportMapping, ImportReport, ImportRowResult
from app.services.base import BaseService
from app.services.parse import parse_schema
from app.services.student_service import StudentService


class ImportService(BaseService):
    entity_type = "import_job"

    def __init__(self, session):
        super().__init__(session)
        self.groups = GroupRepository(session)
        self.students = StudentRepository(session)
        self.student_service = StudentService(session)

    def preview_import(
        self,
        path: str | Path,
        mapping: ImportMapping | dict | None = None,
        group_id: int | None = None,
    ) -> ImportReport:
        if group_id is None:
            raise ValidationError("group_id is required for student import")
        self.groups.get_or_raise(group_id, "Group")
        map_cfg = parse_schema(ImportMapping, mapping or {})
        _headers, rows = read_tabular(Path(path))
        report = self._build_report(rows, map_cfg, group_id)
        job = ImportJob(
            source_path=str(path),
            status=ImportJobStatus.PREVIEW if report.valid else ImportJobStatus.FAILED,
            group_id=group_id,
            report_json=report.model_dump_json(),
        )
        self.session.add(job)
        self.flush()
        report.job_id = job.id
        job.report_json = report.model_dump_json()
        self.commit()
        return report

    def validate_import(self, job_id: int) -> ImportReport:
        job = self._get_job(job_id)
        report = ImportReport.model_validate_json(job.report_json or "{}")
        if not report.valid:
            raise ValidationError("import has errors; fix file before execute")
        job.status = ImportJobStatus.VALIDATED
        self.commit()
        report.job_id = job.id
        return report

    def execute_import(self, job_id: int) -> ImportReport:
        job = self._get_job(job_id)
        report = ImportReport.model_validate_json(job.report_json or "{}")
        if not report.valid:
            raise ValidationError("cannot execute invalid import")
        if job.group_id is None:
            raise ValidationError("group_id missing on import job")
        created = 0
        try:
            for row in report.rows:
                if row.action != "create":
                    continue
                self.student_service.create({**row.data, "group_id": job.group_id})
                created += 1
            report.to_create = created
            job.status = ImportJobStatus.COMPLETED
            job.report_json = report.model_dump_json()
            self.commit()
        except Exception as exc:
            self.session.rollback()
            job = self._get_job(job_id)
            job.status = ImportJobStatus.FAILED
            report.errors.append(str(exc))
            report.valid = False
            job.report_json = report.model_dump_json()
            self.commit()
            raise ValidationError(str(exc)) from exc
        report.job_id = job.id
        return report

    def get_import_report(self, job_id: int) -> ImportReport:
        job = self._get_job(job_id)
        report = ImportReport.model_validate_json(job.report_json or "{}")
        report.job_id = job.id
        return report

    def _build_report(
        self, rows: list[dict], mapping: ImportMapping, group_id: int
    ) -> ImportReport:
        results: list[ImportRowResult] = []
        errors: list[str] = []
        warnings: list[str] = []
        to_create = 0
        seen_numbers: set[str] = set()

        for idx, raw in enumerate(rows, start=2):
            number = (raw.get(mapping.student_number) or "").strip()
            last_name = (raw.get(mapping.last_name) or "").strip()
            first_name = (raw.get(mapping.first_name) or "").strip()
            if not number or not last_name or not first_name:
                msg = f"row {idx}: missing required fields"
                errors.append(msg)
                results.append(
                    ImportRowResult(
                        row_index=idx, action="error", student_number=number or None, message=msg
                    )
                )
                continue
            if number in seen_numbers:
                msg = f"row {idx}: duplicate student_number in file"
                errors.append(msg)
                results.append(
                    ImportRowResult(
                        row_index=idx, action="error", student_number=number, message=msg
                    )
                )
                continue
            seen_numbers.add(number)
            existing = self.students.get_by_number(number)
            if existing:
                msg = f"row {idx}: student_number already exists"
                results.append(
                    ImportRowResult(
                        row_index=idx, action="skip", student_number=number, message=msg
                    )
                )
                warnings.append(msg)
                continue
            fio_match = self.session.scalar(
                select(Student).where(
                    Student.last_name == last_name,
                    Student.first_name == first_name,
                    Student.is_archived.is_(False),
                )
            )
            data = {
                "student_number": number,
                "last_name": last_name,
                "first_name": first_name,
                "group_id": group_id,
            }
            if mapping.middle_name and raw.get(mapping.middle_name):
                data["middle_name"] = str(raw.get(mapping.middle_name)).strip()
            if mapping.email and raw.get(mapping.email):
                data["email"] = str(raw.get(mapping.email)).strip()
            if mapping.phone and raw.get(mapping.phone):
                data["phone"] = str(raw.get(mapping.phone)).strip()

            msg = None
            if fio_match:
                msg = f"row {idx}: possible FIO duplicate (id={fio_match.id}); will create new record"
                warnings.append(msg)
            results.append(
                ImportRowResult(
                    row_index=idx,
                    action="create",
                    student_number=number,
                    message=msg,
                    data=data,
                )
            )
            to_create += 1

        return ImportReport(
            valid=len(errors) == 0 and to_create > 0,
            total_rows=len(rows),
            to_create=to_create,
            warnings=warnings,
            errors=errors,
            rows=results,
        )

    def _get_job(self, job_id: int) -> ImportJob:
        job = self.session.get(ImportJob, job_id)
        if job is None:
            raise NotFoundError(f"ImportJob id={job_id} not found")
        return job
