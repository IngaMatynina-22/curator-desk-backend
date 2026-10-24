from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import ImportJobStatus
from app.database.base import Base
from app.models.mixins import TimestampMixin


class ImportJob(Base, TimestampMixin):
    __tablename__ = "import_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_path: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ImportJobStatus.PREVIEW, index=True
    )
    group_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    report_json: Mapped[str | None] = mapped_column(Text, nullable=True)
