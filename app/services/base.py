"""Base service helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.enums import AuditOperation
from app.core.exceptions import ConflictError, DatabaseError, ValidationError
from app.services.audit_hooks import write_audit

T = TypeVar("T")


class BaseService:
    entity_type: str = "entity"

    def __init__(self, session: Session) -> None:
        self.session = session

    def commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError(str(exc.orig) if exc.orig else str(exc)) from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError(str(exc)) from exc

    def flush(self) -> None:
        try:
            self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError(str(exc.orig) if exc.orig else str(exc)) from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError(str(exc)) from exc

    def audit(
        self,
        entity_id: int,
        operation: AuditOperation | str,
        changes: dict[str, Any] | None = None,
    ) -> None:
        write_audit(
            self.session,
            entity_type=self.entity_type,
            entity_id=entity_id,
            operation=operation,
            changes=changes,
        )

    @staticmethod
    def require(condition: bool, message: str) -> None:
        if not condition:
            raise ValidationError(message)

    def run_in_transaction(self, fn: Callable[[], T]) -> T:
        try:
            result = fn()
            self.commit()
            return result
        except (ValidationError, ConflictError, DatabaseError):
            self.session.rollback()
            raise
        except Exception:
            self.session.rollback()
            raise
