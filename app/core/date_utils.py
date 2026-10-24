"""Date/time helpers."""

from datetime import date, datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def ensure_not_future(value: date, field_name: str = "date") -> None:
    from app.core.exceptions import ValidationError

    if value > date.today():
        raise ValidationError(f"{field_name} cannot be in the future")


def date_range_valid(start: datetime | date, end: datetime | date | None) -> bool:
    if end is None:
        return True
    return end >= start
