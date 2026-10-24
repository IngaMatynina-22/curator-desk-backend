from __future__ import annotations

from app.core.config import get_settings
from app.core.enums import AuditOperation
from app.core.exceptions import AuthError, ConflictError, ValidationError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthSessionOut, LoginRequest, RegisterRequest, UserOut
from app.services.audit_hooks import write_audit
from app.services.base import BaseService
from app.services.parse import parse_schema
from app.services.settings_service import SettingsService

_SESSION_KEY = "auth.current_user_id"


class AuthService(BaseService):
    entity_type = "user"

    def __init__(self, session):
        super().__init__(session)
        self.repo = UserRepository(session)
        self.settings = SettingsService(session)

    def register(self, data: RegisterRequest | dict) -> UserOut:
        payload = parse_schema(RegisterRequest, data)
        if self.repo.get_by_username(payload.username):
            raise ConflictError(f"username already taken: {payload.username}")
        if payload.email and self.repo.get_by_email(payload.email):
            raise ConflictError(f"email already taken: {payload.email}")
        try:
            password_hash = hash_password(payload.password)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        user = User(
            username=payload.username,
            email=payload.email,
            full_name=payload.full_name,
            password_hash=password_hash,
            role=payload.role,
            is_active=True,
        )
        self.repo.add(user)
        write_audit(
            self.session,
            entity_type=self.entity_type,
            entity_id=user.id,
            operation=AuditOperation.CREATE,
            changes={"username": user.username, "role": user.role},
            operator_name=user.username,
        )
        self.commit()
        return UserOut.model_validate(user)

    def login(self, data: LoginRequest | dict) -> AuthSessionOut:
        payload = parse_schema(LoginRequest, data)
        user = self.repo.get_by_username(payload.username.strip().lower())
        if user is None or not user.is_active or user.is_archived:
            raise AuthError("invalid username or password")
        if not verify_password(payload.password, user.password_hash):
            raise AuthError("invalid username or password")
        self._set_session(user)
        return AuthSessionOut(user=UserOut.model_validate(user), message="logged_in")

    def logout(self) -> None:
        # Avoid SettingsService.commit side-effects mid-transaction; write directly.
        self.settings.set(_SESSION_KEY, None)
        get_settings().operator_name = "curator"

    def current_user(self) -> UserOut | None:
        user_id = self.settings.get(_SESSION_KEY)
        if user_id is None:
            return None
        user = self.repo.get(int(user_id))
        if user is None or not user.is_active or user.is_archived:
            return None
        return UserOut.model_validate(user)

    def require_user(self) -> UserOut:
        user = self.current_user()
        if user is None:
            raise AuthError("authentication required")
        return user

    def change_password(self, user_id: int, old_password: str, new_password: str) -> UserOut:
        user = self.repo.get_or_raise(user_id, "User")
        if not verify_password(old_password, user.password_hash):
            raise AuthError("invalid current password")
        try:
            user.password_hash = hash_password(new_password)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.flush()
        write_audit(
            self.session,
            entity_type=self.entity_type,
            entity_id=user.id,
            operation=AuditOperation.UPDATE,
            changes={"password": {"redacted": True}},
            operator_name=user.username,
        )
        self.commit()
        return UserOut.model_validate(user)

    def _set_session(self, user: User) -> None:
        self.settings.set(_SESSION_KEY, user.id)
        get_settings().operator_name = user.username
