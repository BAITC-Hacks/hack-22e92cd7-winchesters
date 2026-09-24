"""COM-01: the committee override ledger.

What these pin: an override needs a reason code (and a note for "other");
only committee and admin may read or write overrides; history comes back
oldest first with who, when, from and to; each override writes an audit row;
the rows cannot be updated or deleted; and the AI's level is never written
over, nor taken from the client when the server has one stored.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from backend.db.candidates import applicant_id_for
from backend.db.overrides import AUDIT_OBJECT_TYPE, parse_reason
from backend.db.tables import AuditLogEntry, CommitteeOverrideRecord, CompetencyScore, PromptVersion, RubricVersion

URL = "/api/overrides/c-001"


def _body(**overrides):
    body = {"competency": "teamwork", "to_level": "high", "reason_code": "interview_evidence", "ai_level": "normal"}
    body.update(overrides)
    return {k: v for k, v in body.items() if v is not None}


@pytest.fixture
def committee(auth_headers):
    return auth_headers("committee")


# ── Reason code ────────────────────────────────────────────────────


def test_reason_code_is_required(client, committee):
    response = client.post(URL, headers=committee, json=_body(reason_code=None))
    assert response.status_code == 422
    assert client.get(URL, headers=committee).json()["overrides"] == []


def test_unknown_reason_code_is_rejected(client, committee):
    assert client.post(URL, headers=committee, json=_body(reason_code="felt_like_it")).status_code == 422


def test_other_needs_a_note(client, committee):
    assert client.post(URL, headers=committee, json=_body(reason_code="other", note="  ")).status_code == 422
    response = client.post(URL, headers=committee, json=_body(reason_code="other", note="Panel consensus"))
    assert response.status_code == 201, response.text
    assert response.json()["reason_code"] == "other"
    assert response.json()["note"] == "Panel consensus"


def test_reason_codes_are_listed(client, committee):
    codes = {c["code"]: c for c in client.get("/api/overrides/reason-codes", headers=committee).json()}
    assert "interview_evidence" in codes
    assert codes["other"]["note_required"] is True


def test_level_must_be_a_bars_level(client, committee):
    assert client.post(URL, headers=committee, json=_body(to_level="87")).status_code == 422


# ── Who may ────────────────────────────────────────────────────────


@pytest.mark.parametrize("role", ["applicant", "interviewer"])
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_non_committee_roles_get_403(client, auth_headers, role, method):
    headers = auth_headers(role, owns="c-001") if role == "applicant" else auth_headers(role)
    response = client.request(method, URL, headers=headers, json=_body())
    assert response.status_code == 403


def test_admin_may_override(client, auth_headers):
    assert client.post(URL, headers=auth_headers("admin"), json=_body()).status_code == 201


def test_unknown_candidate_is_404(client, committee):
    assert client.post("/api/overrides/c-999", headers=committee, json=_body()).status_code == 404
    assert client.get("/api/overrides/c-999", headers=committee).status_code == 404


# ── History ────────────────────────────────────────────────────────


def test_history_is_in_order_with_authors(client, auth_headers):
    first, second = auth_headers("committee"), auth_headers("admin")
    assert client.post(URL, headers=first, json=_body(to_level="high")).status_code == 201
    assert client.post(URL, headers=second, json=_body(to_level="weak", reason_code="evidence_misread")).status_code == 201
    # Another competency and another applicant do not leak into this history.
    client.post(URL, headers=first, json=_body(competency="values"))
    client.post("/api/overrides/c-002", headers=first, json=_body())

    overrides = [o for o in client.get(URL, headers=first).json()["overrides"] if o["competency"] == "teamwork"]
    assert [(o["from_level"], o["to_level"]) for o in overrides] == [("normal", "high"), ("high", "weak")]
    assert [o["author"]["role"] for o in overrides] == ["committee", "admin"]
    assert [o["reason_code"] for o in overrides] == ["interview_evidence", "evidence_misread"]
    # The AI level stays what the card showed, under both overrides.
    assert {(o["ai_level"], o["ai_level_source"]) for o in overrides} == {("normal", "client")}
    assert overrides[0]["created_at"] <= overrides[1]["created_at"]


def test_an_override_that_changes_nothing_is_refused(client, committee):
    assert client.post(URL, headers=committee, json=_body(to_level="normal")).status_code == 409
    client.post(URL, headers=committee, json=_body(to_level="high"))
    assert client.post(URL, headers=committee, json=_body(to_level="high")).status_code == 409


def test_human_rated_competency_has_no_from_level(client, committee):
    body = _body(competency="wounded_leadership", ai_level=None, reason_code="human_rated")
    response = client.post(URL, headers=committee, json=body)
    assert response.status_code == 201
    assert response.json()["from_level"] is None
    assert response.json()["ai_level_source"] == "none"


def test_each_override_writes_an_audit_row_without_the_note(client, db, committee):
    created = client.post(URL, headers=committee, json=_body(note="Said so in the interview")).json()
    with Session(db) as session:
        [audit] = session.exec(select(AuditLogEntry).where(AuditLogEntry.object_id == created["id"])).all()
    assert audit.object_type == AUDIT_OBJECT_TYPE
    assert audit.actor_user_id == created["author"]["id"]
    assert audit.before == {"level": "normal", "ai_level": "normal", "ai_level_source": "client"}
    assert audit.after["level"] == "high"
    assert audit.after["reason_code"] == "interview_evidence"
    assert "Said so" not in str(audit.before) + str(audit.after)


def test_reason_without_a_code_parses_as_a_note():
    assert parse_reason("interview_evidence: seen live") == ("interview_evidence", "seen live")
    assert parse_reason("other") == ("other", "")
    assert parse_reason("Interview did not confirm it.") == (None, "Interview did not confirm it.")


# ── Append-only ────────────────────────────────────────────────────


@pytest.mark.parametrize("table", ["committee_overrides", "audit_log"])
def test_rows_written_by_the_api_cannot_be_updated_or_deleted(client, db, committee, table):
    override_id = client.post(URL, headers=committee, json=_body()).json()["id"]
    column = "id" if table == "committee_overrides" else "object_id"
    with db.begin() as connection, pytest.raises(IntegrityError, match=f"{table} is append-only"):
        connection.execute(text(f"UPDATE {table} SET created_at = created_at WHERE {column} = :id"), {"id": override_id})
    with db.begin() as connection, pytest.raises(IntegrityError, match=f"{table} is append-only"):
        connection.execute(text(f"DELETE FROM {table} WHERE {column} = :id"), {"id": override_id})


# ── The AI row ─────────────────────────────────────────────────────


@pytest.fixture
def stored_ai_level(db):
    """A stored AI level of `high` for c-001's teamwork."""
    with Session(db) as session:
        rubric = RubricVersion(version="provisional-0.1", content_hash="a" * 64)
        prompt = PromptVersion(version="led-04.0", content_hash="b" * 64)
        session.add_all([rubric, prompt])
        session.flush()
        score = CompetencyScore(
            applicant_id=applicant_id_for("c-001"),
            competency="teamwork",
            level="high",
            rule_applied="R1",
            schema_version="led-03.1",
            rubric_version_id=rubric.id,
            prompt_version_id=prompt.id,
            model_judge="judge",
            model_extract="extract",
        )
        session.add(score)
        session.commit()
        return score.id


def test_stored_ai_level_wins_over_the_client_and_is_never_overwritten(client, db, committee, stored_ai_level):
    # The client claims the AI said weak; the server has high on record.
    response = client.post(URL, headers=committee, json=_body(to_level="normal", ai_level="weak"))
    assert response.status_code == 201
    assert response.json()["from_level"] == "high"
    assert (response.json()["ai_level"], response.json()["ai_level_source"]) == ("high", "ledger")

    with Session(db) as session:
        assert session.get(CompetencyScore, stored_ai_level).level == "high"
        overrides = session.exec(select(CommitteeOverrideRecord)).all()
    assert [o.to_level for o in overrides] == ["normal"]
