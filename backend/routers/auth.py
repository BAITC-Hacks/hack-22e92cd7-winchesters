"""Authentication endpoints — register, login, profile.

Simple JWT-based auth for hackathon. Users stored in memory.
Each registered user gets linked to a candidate ID when they submit an application.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import time

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ── Simple JWT-like token system ────────────────────────────────────

_SECRET = os.environ.get("AUTH_SECRET", "invisionu-hackathon-secret-2026")
_security = HTTPBearer(auto_error=False)


def _hash_password(password: str) -> str:
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
    if not user_id or user_id not in _users:
        return None
    return _users[user_id]


# ── In-memory user store ────────────────────────────────────────────

_users: dict[str, dict] = {}


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
    # Check if email already taken
    for u in _users.values():
        if u["email"] == req.email:
            raise HTTPException(status_code=400, detail="Email already registered")

    user_id = f"u-{secrets.token_hex(4)}"
    hashed = _hash_password(req.password)

    user = {
        "id": user_id,
        "email": req.email,
        "full_name": req.full_name,
        "password_hash": hashed,
        "candidate_id": None,
        "role": "applicant",
    }
    _users[user_id] = user

    token = _create_token(user_id)
    return AuthResponse(
        token=token,
        user={
            "id": user_id,
            "email": req.email,
            "full_name": req.full_name,
            "candidate_id": None,
            "role": "applicant",
        },
    )


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest):
    """Login with email and password."""
    hashed = _hash_password(req.password)

    for u in _users.values():
        if u["email"] == req.email and u["password_hash"] == hashed:
            token = _create_token(u["id"])
            return AuthResponse(
                token=token,
                user={
                    "id": u["id"],
                    "email": u["email"],
                    "full_name": u["full_name"],
                    "candidate_id": u.get("candidate_id"),
                    "role": u.get("role", "applicant"),
                },
            )

    raise HTTPException(status_code=401, detail="Invalid email or password")


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
    user["candidate_id"] = candidate_id
    return {"status": "ok", "candidate_id": candidate_id}


# ── Pre-seed a committee account for demo ───────────────────────────

def _seed_demo_users():
    """Create demo accounts for the hackathon presentation."""
    committee_id = "u-committee"
    if committee_id not in _users:
        _users[committee_id] = {
            "id": committee_id,
            "email": "committee@invisionu.edu",
            "full_name": "Admissions Committee",
            "password_hash": _hash_password("demo2026"),
            "candidate_id": None,
            "role": "committee",
        }

_seed_demo_users()
