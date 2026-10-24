"""Domain exceptions for CuratorDesk."""


class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str = "Application error") -> None:
        self.message = message
        super().__init__(message)


class ValidationError(AppError):
    """Invalid input or business rule violation."""


class NotFoundError(AppError):
    """Requested entity was not found."""


class ConflictError(AppError):
    """Conflict with existing data or state."""


class DatabaseError(AppError):
    """Database or persistence failure."""


class AuthError(AppError):
    """Authentication or authorization failure."""
