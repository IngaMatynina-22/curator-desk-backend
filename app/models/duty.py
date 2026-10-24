from __future__ import annotations

from datetime import date, time
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import DutyStatus
from app.database.base import Base
from app.models.associations import DutyStudent
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.student import Student


class Duty(Base, TimestampMixin):
    __tablename__ = "duties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    duty_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    duty_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=DutyStatus.PLANNED, index=True
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    student_links: Mapped[list[DutyStudent]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def student_ids(self) -> list[int]:
        return [link.student_id for link in self.student_links]
