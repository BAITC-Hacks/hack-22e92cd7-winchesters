"""Append-only committee signature workflow."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlmodel import Session, col, select

from backend.db.candidates import applicant_id_for
from backend.db.engine import get_engine
from backend.db.tables import AuditLogEntry, CommitteeSignatureRecord, User


class SignatureAlreadyRecorded(ValueError):
    pass


def list_signatures(candidate_ref: str) -> list[dict[str, Any]]:
    applicant_id = applicant_id_for(candidate_ref)
    if applicant_id is None:
        return []
    with Session(get_engine()) as session:
        rows = session.exec(
            select(CommitteeSignatureRecord)
            .where(col(CommitteeSignatureRecord.applicant_id) == applicant_id)
            .order_by(col(CommitteeSignatureRecord.created_at))
        ).all()
        return [{
            "role": row.role, "name": row.signer_name, "signed_at": _aware(row.created_at).isoformat(),
        } for row in rows]


def record_signature(candidate_ref: str, role: str, user_id: str) -> None:
    applicant_id = applicant_id_for(candidate_ref)
    if applicant_id is None:
        raise ValueError(f"candidate {candidate_ref} does not exist")
    with Session(get_engine()) as session:
        exists = session.exec(select(CommitteeSignatureRecord).where(
            col(CommitteeSignatureRecord.applicant_id) == applicant_id,
            col(CommitteeSignatureRecord.role) == role,
        )).first()
        if exists is not None:
            raise SignatureAlreadyRecorded(role)
        user = session.get(User, user_id)
        if user is None:
            raise ValueError("signer does not exist")
        signature = CommitteeSignatureRecord(
            applicant_id=applicant_id, role=role, signer_user_id=user_id, signer_name=user.full_name,
        )
        session.add(signature)
        session.flush()
        session.add(AuditLogEntry(
            actor_user_id=user_id, action="committee_signature.create", object_type="committee_signature",
            object_id=signature.id, before=None,
            after={"applicant_id": applicant_id, "role": role},
        ))
        session.commit()


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)