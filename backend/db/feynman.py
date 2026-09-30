"""Scenario sessions and results (INP-03 storage, INP-04 results).

Every function is one unit of work with its own session; from `async def`
routes call them through `run_in_threadpool`. The writes that race (a second
start, a double-sent message, a double-clicked Finish) are single conditional
statements, so SQLite decides the winner and the loser gets `False`/`None`
instead of a lost update.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, func, insert, literal, update
from sqlmodel import Session, col, select

from backend.db.engine import get_engine
from backend.db.tables import FeynmanSession, FeynmanStatus, ScenarioResult


def _session_dict(row: FeynmanSession) -> dict[str, Any]:
    return {
        "id": row.id,
        "applicant_id": row.applicant_id,
        "user_id": row.user_id,
        "topic_id": row.topic_id,
        "language": row.language,
        "messages": list(row.messages),
        "exchange_count": row.exchange_count,
        "status": row.status,
    }


def _result_dict(row: ScenarioResult) -> dict[str, Any]:
    return {
        "session_id": row.session_id,
        "applicant_id": row.applicant_id,
        "competency": row.competency,
        "rating": dict(row.rating),
        "source": row.source,
        "model": row.model,
    }


def _attempts_of(applicant_id: str):
    return (
        select(func.count())
        .select_from(FeynmanSession)
        .where(col(FeynmanSession.applicant_id) == applicant_id)
        .scalar_subquery()
    )


# ── Reads ──────────────────────────────────────────────────────────


def attempts_used(applicant_id: str) -> int:
    with Session(get_engine()) as session:
        return session.exec(select(_attempts_of(applicant_id))).one()


def get_session(session_id: str) -> dict[str, Any] | None:
    with Session(get_engine()) as session:
        row = session.get(FeynmanSession, session_id)
        return _session_dict(row) if row else None


def latest_result(applicant_id: str) -> dict[str, Any] | None:
    """The most recent finished scenario's result, if any."""
    with Session(get_engine()) as session:
        row = session.exec(
            select(ScenarioResult)
            .where(col(ScenarioResult.applicant_id) == applicant_id)
            .order_by(col(ScenarioResult.created_at).desc())
        ).first()
        return _result_dict(row) if row else None


# ── Writes ─────────────────────────────────────────────────────────


def create_session(
    applicant_id: str,
    user_id: str,
    topic_id: str,
    messages: list[dict[str, str]],
    max_attempts: int,
    language: str = "en",
) -> dict[str, Any] | None:
    """Store a new attempt, or return None if the applicant has used them all.

    The count and the insert are one statement (INSERT ... SELECT ... WHERE
    count < limit), so two starts racing from two tabs cannot both take the
    last attempt. Any attempt the applicant left open is closed as abandoned:
    one live conversation at a time.
    """
    session_id = str(uuid.uuid4())
    table = FeynmanSession.__table__
    values = {
        "id": literal(session_id, String),
        "applicant_id": literal(applicant_id, String),
        "user_id": literal(user_id, String),
        "topic_id": literal(topic_id, String),
        "language": literal(language, String),
        "messages": literal(messages, JSON),
        "exchange_count": literal(1, Integer),
        "status": literal(FeynmanStatus.ACTIVE.value, String),
        "created_at": literal(datetime.now(UTC), DateTime(timezone=True)),
    }
    with Session(get_engine()) as session:
        inserted = session.execute(
            insert(table).from_select(
                list(values),
                select(*values.values()).where(_attempts_of(applicant_id) < max_attempts),
            )
        )
        if inserted.rowcount != 1:
            session.rollback()
            return None
        session.execute(
            update(FeynmanSession)
            .where(
                col(FeynmanSession.applicant_id) == applicant_id,
                col(FeynmanSession.status) == FeynmanStatus.ACTIVE.value,
                col(FeynmanSession.id) != session_id,
            )
            .values(status=FeynmanStatus.ABANDONED.value)
        )
        session.commit()
        return _session_dict(session.get(FeynmanSession, session_id))


def record_exchange(session_id: str, seen_count: int, messages: list[dict[str, str]]) -> bool:
    """Save a turn, if the session is still active and still at `seen_count`.

    False means another request got there first (a double-sent message), and
    this turn must not overwrite it.
    """
    with Session(get_engine()) as session:
        result = session.execute(
            update(FeynmanSession)
            .where(
                col(FeynmanSession.id) == session_id,
                col(FeynmanSession.status) == FeynmanStatus.ACTIVE.value,
                col(FeynmanSession.exchange_count) == seen_count,
            )
            .values(messages=messages, exchange_count=seen_count + 1)
        )
        session.commit()
        return result.rowcount == 1


def _move(session_id: str, source: FeynmanStatus, target: FeynmanStatus) -> bool:
    with Session(get_engine()) as session:
        result = session.execute(
            update(FeynmanSession)
            .where(col(FeynmanSession.id) == session_id, col(FeynmanSession.status) == source.value)
            .values(status=target.value)
        )
        session.commit()
        return result.rowcount == 1


def claim_for_scoring(session_id: str) -> bool:
    """active -> scoring. False if it is already being scored or is closed."""
    return _move(session_id, FeynmanStatus.ACTIVE, FeynmanStatus.SCORING)


def release_scoring(session_id: str) -> None:
    """scoring -> active, after the scorer failed, so the applicant can retry."""
    _move(session_id, FeynmanStatus.SCORING, FeynmanStatus.ACTIVE)


def save_result(session_id: str, competency: str, rating: dict[str, Any], source: str, model: str) -> None:
    """Store the rating and close the session, in one transaction."""
    with Session(get_engine()) as session:
        row = session.get(FeynmanSession, session_id)
        session.add(
            ScenarioResult(
                session_id=session_id, applicant_id=row.applicant_id, competency=competency, rating=rating, source=source, model=model
            )
        )
        row.status = FeynmanStatus.FINISHED.value
        row.finished_at = datetime.now(UTC)
        session.add(row)
        session.commit()
