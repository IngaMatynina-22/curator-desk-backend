"""Password hashing helpers (PBKDF2, stdlib)."""

from __future__ import annotations

import hashlib
import hmac
import secrets

_ALGORITHM = "sha256"
_ITERATIONS = 120_000
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    if not password or len(password) < 6:
        raise ValueError("password must be at least 6 characters")
    salt = secrets.token_hex(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        _ALGORITHM, password.encode("utf-8"), salt.encode("utf-8"), _ITERATIONS
    ).hex()
    return f"pbkdf2_{_ALGORITHM}${_ITERATIONS}${salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algo, iterations_s, salt, digest = password_hash.split("$", 3)
        if not algo.startswith("pbkdf2_"):
            return False
        iterations = int(iterations_s)
        candidate = hashlib.pbkdf2_hmac(
            _ALGORITHM, password.encode("utf-8"), salt.encode("utf-8"), iterations
        ).hex()
        return hmac.compare_digest(candidate, digest)
    except (ValueError, TypeError):
        return False
