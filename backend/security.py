"""Password hashing, access tokens and roles (FND-05).

Pure functions over strings: no FastAPI, no database. The seed hashes the demo
password with this module and the routers verify with it, so neither depends on
the other. The request guards built on top of it live in
`backend/routers/guards.py`.

Replaces the hackathon scheme: unsalted SHA-256 password hashes and a
home-made token with no expiry. Old hashes are not migrated; they simply fail
verification (`python -m backend.db reset` rebuilds a local database).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from backend import settings


class Role(StrEnum):
    APPLICANT = "applicant"
    INTERVIEWER = "interviewer"
    COMMITTEE = "committee"
    ADMIN = "admin"


ALL_ROLES = tuple(Role)
# Everyone who works on applications rather than submitting one.
STAFF_ROLES = (Role.INTERVIEWER, Role.COMMITTEE, Role.ADMIN)


# ── Passwords ──────────────────────────────────────────────────────

# argon2id with the library's defaults (RFC 9106 low-memory profile). The
# parameters are stored in each hash, so raising them later only needs
# `needs_rehash` on the next login, not a migration.
_hasher = PasswordHasher()
_dummy_hash: str | None = None


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        # InvalidHashError covers pre-FND-05 SHA-256 hex digests.
        return False


def needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def burn_verify_time(password: str) -> None:
    """Spend the time of one real verification.

    Login calls this when the email is unknown, so response time does not tell
    an attacker which emails have accounts.
    """
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = _hasher.hash("not-a-real-password")
    verify_password(_dummy_hash, password)


# ── Secret ─────────────────────────────────────────────────────────

# backend/.env.example ships a secret with this prefix so a fresh checkout runs
# the demo. It is refused outside DEMO_MODE: a secret everyone can read in the
# repository signs tokens anyone can forge.
DEV_SECRET_PREFIX = "dev-only-"
_MIN_SECRET_LENGTH = 32


class AuthConfigError(RuntimeError):
    pass


def check_auth_config() -> None:
    """Raise unless AUTH_SECRET is usable. Called at startup and per token."""
    secret = settings.AUTH_SECRET
    if not secret:
        raise AuthConfigError(
            "AUTH_SECRET is not set. Copy it from backend/.env.example for local demo "
            'use, or generate one: python -c "import secrets; print(secrets.token_urlsafe(48))"'
        )
    if len(secret) < _MIN_SECRET_LENGTH:
        raise AuthConfigError(f"AUTH_SECRET must be at least {_MIN_SECRET_LENGTH} characters")
    if secret.startswith(DEV_SECRET_PREFIX) and not settings.DEMO_MODE:
        raise AuthConfigError(
            f"AUTH_SECRET starting with '{DEV_SECRET_PREFIX}' is only accepted with DEMO_MODE=1"
        )


def _secret() -> str:
    check_auth_config()
    return settings.AUTH_SECRET


# ── Tokens ─────────────────────────────────────────────────────────

_ALGORITHM = "HS256"


def create_access_token(user_id: str, role: str, *, now: datetime | None = None) -> str:
    issued = now or datetime.now(UTC)
    payload = {
        "sub": user_id,
        # Informational, for the client. Guards read the role from the
        # database, so demoting a user takes effect before their token expires.
        "role": role,
        "iat": issued,
        "exp": issued + timedelta(minutes=settings.AUTH_TOKEN_TTL_MINUTES),
    }
    return jwt.encode(payload, _secret(), algorithm=_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """The user id a valid, unexpired token was issued to; None otherwise."""
    try:
        claims = jwt.decode(
            token,
            _secret(),
            algorithms=[_ALGORITHM],
            options={"require": ["sub", "exp", "iat"]},
        )
    except jwt.InvalidTokenError:
        return None
    return claims["sub"]
