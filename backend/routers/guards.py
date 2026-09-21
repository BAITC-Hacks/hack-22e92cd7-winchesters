"""Request guards (FND-05): who is calling, and may they touch this record.

Every route outside `/api/auth/register` and `/api/auth/login` depends on
`require_role(...)`; `tests/test_auth.py` walks the app's routes to keep it
that way. Guards are sync `def` dependencies, so FastAPI runs their database
lookup in the threadpool.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.db import candidates as candidate_store
from backend.db import users as user_store
from backend.security import STAFF_ROLES, Role, decode_access_token

_bearer = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict[str, Any]:
    if credentials is None:
        raise _unauthorized("Not authenticated")
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise _unauthorized("Invalid or expired token")
    user = user_store.get_user(user_id)
    if user is None:
        raise _unauthorized("Invalid or expired token")
    return user


def require_role(*roles: Role) -> Callable[..., dict[str, Any]]:
    """Dependency: the current user, if their role is one of `roles`."""
    allowed = frozenset(roles)

    def dependency(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
        if user["role"] not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed for your role")
        return user

    return dependency


def ensure_candidate_access(user: dict[str, Any], candidate_ref: str) -> None:
    """Object-level check: staff see every candidate, an applicant only their own.

    Raises 403 for someone else's record and for one that does not exist, so an
    applicant cannot probe which ids are taken. Sync: from an `async def`
    route, call through `run_in_threadpool`.
    """
    if user["role"] in STAFF_ROLES:
        return
    own = user.get("applicant_id")
    if own is None or candidate_store.applicant_id_for(candidate_ref) != own:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your application")
