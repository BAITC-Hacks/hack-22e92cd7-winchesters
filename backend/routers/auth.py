"""Authentication endpoints: register, login, profile.

Passwords are argon2id and tokens are JWTs with an expiry (`backend/security.py`);
the guards every other router uses are in `backend/routers/guards.py`.
Registration always creates an applicant. Staff accounts are made with
`python -m backend.db create-user`, and the demo committee account exists (and
can log in) only under DEMO_MODE.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from backend import settings
from backend.db import users as store
from backend.db.seed import DEMO_EMAILS
from backend.routers.guards import ensure_candidate_access, require_role
from backend.security import (
    ALL_ROLES,
    Role,
    burn_verify_time,
    create_access_token,
    hash_password,
    needs_rehash,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Request/Response models ─────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)
    full_name: str = Field(min_length=1, max_length=200)


class LoginRequest(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(max_length=256)


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    candidate_id: str | None = None
    role: Role


class AuthResponse(BaseModel):
    token: str
    user: UserProfile


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _profile(user: dict[str, Any]) -> UserProfile:
    return UserProfile(
        id=user["id"],
        email=user["email"],
        full_name=user["full_name"],
        candidate_id=user.get("candidate_id"),
        role=user["role"],
    )


def _auth_response(user: dict[str, Any]) -> AuthResponse:
    return AuthResponse(token=create_access_token(user["id"], user["role"]), user=_profile(user))


# ── Endpoints ───────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest):
    """Register a new applicant account. Public."""
    try:
        user = store.create_user(
            _normalize_email(req.email), hash_password(req.password), req.full_name.strip(), role=Role.APPLICANT.value
        )
    except store.EmailTaken:
        raise HTTPException(status_code=400, detail="Email already registered")
    return _auth_response(user)


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest):
    """Log in with email and password. Public."""
    email = _normalize_email(req.email)
    # A database built under DEMO_MODE keeps the demo rows after the flag is
    # turned off; the accounts must stop working anyway.
    user = None if email in DEMO_EMAILS and not settings.DEMO_MODE else store.get_user_by_email(email)
    if user is None:
        burn_verify_time(req.password)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not verify_password(user["password_hash"], req.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if needs_rehash(user["password_hash"]):
        store.set_password_hash(user["id"], hash_password(req.password))
    return _auth_response(user)


@router.get("/me", response_model=UserProfile)
def get_profile(user: dict = Depends(require_role(*ALL_ROLES))):
    """Current user's profile."""
    return _profile(user)


@router.post("/link-candidate")
async def link_candidate(candidate_id: str, user: dict = Depends(require_role(Role.APPLICANT))):
    """Confirm the application `candidate_id` belongs to the caller.

    `POST /api/candidates/` links a new application to its author, so this no
    longer attaches arbitrary records: it used to let any user claim, and then
    read, someone else's application. Kept, idempotent, for clients that still
    call it after submitting.
    """
    await run_in_threadpool(ensure_candidate_access, user, candidate_id)
    return {"status": "ok", "candidate_id": user["candidate_id"]}
