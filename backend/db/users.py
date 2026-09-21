"""User accounts.

Returns plain dicts shaped like the in-memory store this replaces, so the auth
router keeps its logic and only loses its storage. FND-05 rewrites the auth
itself (argon2, JWT, roles); this module is where it will read users from.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from backend.db.candidates import find_applicant
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


def link_candidate(user_id: str, candidate_ref: str) -> str | None:
    """Attach an application to a user. Returns the candidate id, or None if
    no such candidate exists (the old store accepted any string)."""
    with Session(get_engine()) as session:
        user = session.get(User, user_id)
        applicant = find_applicant(session, candidate_ref)
        if user is None or applicant is None:
            return None
        user.applicant_id = applicant.id
        session.add(user)
        session.commit()
        return applicant.legacy_ref or applicant.id
