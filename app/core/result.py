"""Simple result helpers for service responses."""

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class Result(Generic[T]):
    ok: bool
    value: T | None = None
    error: str | None = None
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def success(cls, value: T, warnings: list[str] | None = None) -> "Result[T]":
        return cls(ok=True, value=value, warnings=warnings or [])

    @classmethod
    def failure(cls, error: str) -> "Result[Any]":
        return cls(ok=False, error=error)
