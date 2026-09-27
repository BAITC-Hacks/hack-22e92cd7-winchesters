"""User accounts.

Returns plain dicts. Hashing lives in `backend/security.py`; this module only
stores what it is given. `applicant_id` is the UUID the object-level guards
compare against; `candidate_id` is the id the frontend shows (`c-001`).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from backend.db.engine import get_engine
from backend.db.tables import Applicant, User


class EmailTaken(Exception):
    pass


def _as_dict(session: Session, user: User) -> dict[str, Any]:
    candidate_id = None
    if user.applicant_id:
        applicant = session.get(Applicant, user.applicant_id)
        candidate_id = (applicant.legacy_ref or applicant.id) if applicant else None
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "password_hash": user.password_hash,
        "candidate_id": candidate_id,
        "applicant_id": user.applicant_id,
        "role": user.role,
    }


def get_user(user_id: str) -> dict[str, Any] | None:
    with Session(get_engine()) as session:
        user = session.get(User, user_id)
        return _as_dict(session, user) if user else None


def get_user_by_email(email: str) -> dict[str, Any] | None:
    with Session(get_engine()) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        return _as_dict(session, user) if user else None


def create_user(email: str, password_hash: str, full_name: str, role: str = "applicant") -> dict[str, Any]:
    with Session(get_engine()) as session:
        user = User(email=email, password_hash=password_hash, full_name=full_name, role=role)
        session.add(user)
        try:
            session.commit()
        except IntegrityError as exc:
            raise EmailTaken(email) from exc
        return _as_dict(session, user)


def set_password_hash(user_id: str, password_hash: str) -> None:
    """Replace a hash, e.g. after argon2 parameters are raised."""
    with Session(get_engine()) as session:
        user = session.get(User, user_id)
        if user is not None:
            user.password_hash = password_hash
            session.add(user)
            session.commit()
