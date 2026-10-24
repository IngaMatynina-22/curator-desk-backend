"""Generic repository primitives."""

from __future__ import annotations

from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, entity_id: int) -> ModelT | None:
        return self.session.get(self.model, entity_id)

    def get_or_raise(self, entity_id: int, label: str | None = None) -> ModelT:
        entity = self.get(entity_id)
        if entity is None:
            name = label or self.model.__name__
            raise NotFoundError(f"{name} id={entity_id} not found")
        return entity

    def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity: ModelT) -> None:
        self.session.delete(entity)
        self.session.flush()

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        include_archived: bool = False,
        order_by: Any | None = None,
    ) -> list[ModelT]:
        stmt = select(self.model)
        stmt = self._apply_archive_filter(stmt, include_archived)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        stmt = stmt.offset(offset).limit(limit)
        return list(self.session.scalars(stmt).all())

    def count(self, *, include_archived: bool = False) -> int:
        stmt = select(func.count()).select_from(self.model)
        stmt = self._apply_archive_filter(stmt, include_archived)
        return int(self.session.scalar(stmt) or 0)

    def paginate(
        self,
        stmt: Select[Any],
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[ModelT], int]:
        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        total = int(self.session.scalar(count_stmt) or 0)
        items = list(self.session.scalars(stmt.offset(offset).limit(limit)).all())
        return items, total

    def archive(self, entity: ModelT) -> ModelT:
        if not hasattr(entity, "is_archived"):
            raise TypeError(f"{self.model.__name__} does not support archive")
        entity.is_archived = True  # type: ignore[attr-defined]
        self.session.flush()
        return entity

    def restore(self, entity: ModelT) -> ModelT:
        if not hasattr(entity, "is_archived"):
            raise TypeError(f"{self.model.__name__} does not support restore")
        entity.is_archived = False  # type: ignore[attr-defined]
        self.session.flush()
        return entity

    def _apply_archive_filter(self, stmt: Select[Any], include_archived: bool) -> Select[Any]:
        if include_archived or not hasattr(self.model, "is_archived"):
            return stmt
        return stmt.where(self.model.is_archived.is_(False))  # type: ignore[attr-defined]

    def ensure_ids_exist(self, ids: Sequence[int], label: str = "Entity") -> None:
        if not ids:
            return
        unique_ids = set(ids)
        found = self.session.scalars(
            select(self.model.id).where(self.model.id.in_(unique_ids))  # type: ignore[attr-defined]
        ).all()
        missing = unique_ids - set(found)
        if missing:
            raise NotFoundError(f"{label} ids not found: {sorted(missing)}")
