"""Centralized audit logging."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import SENSITIVE_AUDIT_FIELDS
from app.core.enums import AuditOperation
from app.models.audit_log import AuditLog


def _sanitize_changes(changes: dict[str, Any] | None) -> dict[str, Any] | None:
    if not changes:
        return None
    sanitized: dict[str, Any] = {}
    for key, value in changes.items():
        if key in SENSITIVE_AUDIT_FIELDS:
            sanitized[key] = {"redacted": True}
        else:
            sanitized[key] = value
    return sanitized


def write_audit(
    session: Session,
    *,
    entity_type: str,
    entity_id: int,
    operation: AuditOperation | str,
    changes: dict[str, Any] | None = None,
    operator_name: str | None = None,
) -> AuditLog:
    payload = _sanitize_changes(changes)
    entry = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        operation=str(operation),
        operator_name=operator_name or get_settings().operator_name,
        changed_fields=json.dumps(payload, ensure_ascii=False, default=str)
        if payload is not None
        else None,
    )
    session.add(entry)
    session.flush()
    return entry


def diff_fields(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    changed: dict[str, Any] = {}
    keys = set(old) | set(new)
    for key in keys:
        if old.get(key) != new.get(key):
            changed[key] = {"old": old.get(key), "new": new.get(key)}
    return changed
