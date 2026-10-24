from __future__ import annotations

from datetime import datetime

from sqlalchemy import or_, select

from app.core.date_utils import utc_now
from app.core.enums import NotificationStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.models.notification import Notification
from app.schemas.notification import NotificationOut
from app.services.base import BaseService


class NotificationService(BaseService):
    entity_type = "notification"

    def get_pending(self) -> list[NotificationOut]:
        now = utc_now()
        stmt = (
            select(Notification)
            .where(
                or_(
                    Notification.status == NotificationStatus.PENDING,
                    (Notification.status == NotificationStatus.SNOOZED)
                    & (Notification.snoozed_until <= now),
                )
            )
            .order_by(Notification.due_at.asc().nulls_last(), Notification.created_at.desc())
        )
        items = list(self.session.scalars(stmt).all())
        # Reactivate expired snoozes
        for n in items:
            if n.status == NotificationStatus.SNOOZED:
                n.status = NotificationStatus.PENDING
                n.snoozed_until = None
        if items:
            self.flush()
            self.commit()
        return [NotificationOut.model_validate(n) for n in items]

    def mark_as_read(self, notification_id: int) -> NotificationOut:
        n = self._get(notification_id)
        n.status = NotificationStatus.READ
        self.commit()
        return NotificationOut.model_validate(n)

    def snooze(self, notification_id: int, until: datetime) -> NotificationOut:
        if until <= utc_now():
            raise ValidationError("snooze until must be in the future")
        n = self._get(notification_id)
        n.status = NotificationStatus.SNOOZED
        n.snoozed_until = until
        self.commit()
        return NotificationOut.model_validate(n)

    def dismiss(self, notification_id: int) -> NotificationOut:
        n = self._get(notification_id)
        n.status = NotificationStatus.DISMISSED
        self.commit()
        return NotificationOut.model_validate(n)

    def upsert(
        self,
        *,
        kind: str,
        source_type: str,
        source_id: int,
        title: str,
        body: str | None = None,
        due_at: datetime | None = None,
    ) -> Notification:
        existing = self.session.scalar(
            select(Notification).where(
                Notification.kind == kind,
                Notification.source_type == source_type,
                Notification.source_id == source_id,
            )
        )
        if existing:
            existing.title = title
            existing.body = body
            existing.due_at = due_at
            if existing.status == NotificationStatus.DISMISSED:
                return existing
            if existing.status == NotificationStatus.READ:
                return existing
            existing.status = NotificationStatus.PENDING
            self.flush()
            return existing
        n = Notification(
            kind=kind,
            source_type=source_type,
            source_id=source_id,
            title=title,
            body=body,
            due_at=due_at,
            status=NotificationStatus.PENDING,
        )
        self.session.add(n)
        self.flush()
        return n

    def generate_due_notifications(self) -> list[NotificationOut]:
        from app.services.reminder_service import ReminderService

        ReminderService(self.session).generate()
        self.commit()
        return self.get_pending()

    def count_pending(self) -> int:
        now = utc_now()
        stmt = select(Notification).where(
            or_(
                Notification.status == NotificationStatus.PENDING,
                (Notification.status == NotificationStatus.SNOOZED)
                & (Notification.snoozed_until <= now),
            )
        )
        return len(list(self.session.scalars(stmt).all()))

    def _get(self, notification_id: int) -> Notification:
        n = self.session.get(Notification, notification_id)
        if n is None:
            raise NotFoundError(f"Notification id={notification_id} not found")
        return n
