"""Authentication endpoints — register, login, profile.

Users are stored in the database (`backend/db/users.py`). The hashing and token
scheme below is still the hackathon one — unsalted SHA-256, tokens that never
expire — and is replaced wholesale by FND-05 (argon2, JWT, role guards).
Each registered user gets linked to a candidate ID when they submit an application.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time

from fastapi import APIRouter, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from backend.db import users as store

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ── Simple JWT-like token system ────────────────────────────────────

_SECRET = os.environ.get("AUTH_SECRET", "invisionu-hackathon-secret-2026")
_security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return hashlib.sha256(f"{_SECRET}:{password}".encode()).hexdigest()


def _create_token(user_id: str) -> str:
    payload = f"{user_id}:{time.time()}"
    sig = hashlib.sha256(f"{_SECRET}:{payload}".encode()).hexdigest()[:16]
    return f"{payload}:{sig}"


def _verify_token(token: str) -> str | None:
    """Returns user_id if valid, None otherwise."""
    try:
        parts = token.rsplit(":", 1)
        if len(parts) != 2:
            return None
        payload, sig = parts
        expected_sig = hashlib.sha256(f"{_SECRET}:{payload}".encode()).hexdigest()[:16]
        if sig != expected_sig:
            return None
        user_id = payload.split(":")[0]
        return user_id
    except Exception:
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(_security)) -> dict | None:
    """Dependency: returns current user dict or None."""
    if not credentials:
        return None
    user_id = _verify_token(credentials.credentials)
    if not user_id:
        return None
    return await run_in_threadpool(store.get_user, user_id)


# ── Request/Response models ─────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=4)
    full_name: str = Field(min_length=1)


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    candidate_id: str | None = None
    role: str = "applicant"  # "applicant" or "committee"


# ── Endpoints ───────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest):
    """Register a new user."""
    try:
        user = store.create_user(req.email, hash_password(req.password), req.full_name)
    except store.EmailTaken:
        raise HTTPException(status_code=400, detail="Email already registered")

    return AuthResponse(
        token=_create_token(user["id"]),
        user={
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "candidate_id": None,
            "role": user["role"],
        },
    )


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest):
    """Login with email and password."""
    u = store.get_user_by_email(req.email)
    if u is None or not hmac.compare_digest(u["password_hash"], hash_password(req.password)):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return AuthResponse(
        token=_create_token(u["id"]),
        user={
            "id": u["id"],
            "email": u["email"],
            "full_name": u["full_name"],
            "candidate_id": u["candidate_id"],
            "role": u["role"],
        },
    )


@router.get("/me", response_model=UserProfile)
async def get_profile(user: dict | None = Depends(get_current_user)):
    """Get current user profile."""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return UserProfile(
        id=user["id"],
        email=user["email"],
        full_name=user["full_name"],
        candidate_id=user.get("candidate_id"),
        role=user.get("role", "applicant"),
    )


@router.post("/link-candidate")
async def link_candidate(candidate_id: str, user: dict | None = Depends(get_current_user)):
    """Link a candidate ID to the authenticated user."""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    linked = await run_in_threadpool(store.link_candidate, user["id"], candidate_id)
    if linked is None:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
    return {"status": "ok", "candidate_id": linked}


# The demo committee account is created by `python -m backend.db init` under
# DEMO_MODE (backend/db/seed.py), not at import time.
