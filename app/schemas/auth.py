from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.enums import UserRole
from app.schemas.common import ORMModel


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    email: str | None = None
    role: UserRole = UserRole.CURATOR

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if " " in cleaned:
            raise ValueError("username must not contain spaces")
        return cleaned

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("invalid email format")
        return value.strip().lower()


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserOut(ORMModel):
    id: int
    username: str
    email: str | None
    full_name: str
    role: str
    is_active: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class AuthSessionOut(BaseModel):
    user: UserOut
    message: str = "ok"
