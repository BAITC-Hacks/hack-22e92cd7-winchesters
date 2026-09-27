"""INP-03, storage half: teaching sessions and scores live in the database.

What these pin: a session and its score survive a restart; each applicant has
a fixed number of attempts, enforced before any model call and atomically;
a failed model call is an HTTP error the browser can read (CORS headers
included) and leaves the session as it was, so the applicant can retry;
Finish scores a session once. Everything runs offline: `backend.llm` is
replaced with fakes.
"""

from __future__ import annotations

import httpx
import anthropic
import pytest
from sqlalchemy import func
from sqlmodel import Session, select

from backend import llm, settings
from backend.db import feynman as store
from backend.db.candidates import applicant_id_for
from backend.db.engine import make_engine, set_engine
from backend.db.tables import FeynmanScoreRecord, FeynmanSession, User
from backend.routers import feynman

ORIGIN = "http://localhost:3000"

SCORE = {
    "clarity": 80,
    "patience": 70,
    "empathy": 75,
    "adaptability": 65,
    "quiz_transfer_score": 60,
    "overall_score": 72,
    "summary": "Explained the tilt of the Earth with a flashlight.",
}
QUIZ = {"answers": [{"question": i, "answer": f"answer {i}", "confident": i != 3} for i in (1, 2, 3)]}


class FakeModel:
    """Stands in for backend.llm. `fail` makes the next calls raise it."""

    def __init__(self) -> None:
        self.chat_calls = 0
        self.json_calls = 0
        self.fail: Exception | None = None

    async def complete_chat(self, messages, system, model=""):
        self.chat_calls += 1
        if self.fail:
            raise self.fail
        return f"Arman reply {self.chat_calls}"

    async def complete_json(self, prompt, schema, system="", model=""):
        self.json_calls += 1
        if self.fail:
            raise self.fail
        return QUIZ if schema is feynman.QUIZ_SCHEMA else SCORE


def _connection_error() -> Exception:
    return anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))


def _rate_limit_error() -> Exception:
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return anthropic.RateLimitError("rate limited", response=httpx.Response(429, request=request), body=None)


@pytest.fixture
def model(monkeypatch) -> FakeModel:
    fake = FakeModel()
    monkeypatch.setattr(llm, "complete_chat", fake.complete_chat)
    monkeypatch.setattr(llm, "complete_json", fake.complete_json)
    # A key is "configured" so start goes live; the no-key path has its own tests.
    monkeypatch.setattr(llm, "is_configured", lambda: True)
    return fake


@pytest.fixture
def applicant(auth_headers) -> dict[str, str]:
    return {**auth_headers("applicant", owns="c-003"), "Origin": ORIGIN}


def _start(client, headers, topic="seasons"):
    return client.post("/api/feynman/start", json={"candidate_id": "c-003", "topic_id": topic}, headers=headers)


def _chat(client, headers, session_id, message="The Earth is tilted."):
    return client.post("/api/feynman/chat", json={"session_id": session_id, "message": message}, headers=headers)


def _finish(client, headers, session_id):
    return client.post(f"/api/feynman/finish?session_id={session_id}", headers=headers)


def _row(db, session_id) -> FeynmanSession:
    with Session(db) as session:
        return session.get(FeynmanSession, session_id)


def _teach(client, headers, turns=3) -> str:
    session_id = _start(client, headers).json()["session_id"]
    for _ in range(turns):
        assert _chat(client, headers, session_id).status_code == 200
    return session_id


# ── Storage ────────────────────────────────────────────────────────


def test_in_memory_stores_are_gone():
    assert not hasattr(feynman, "_sessions")
    assert not hasattr(feynman, "_score_cache")


def test_full_session_is_stored_and_survives_a_restart(client, db, model, applicant, auth_headers):
    session_id = _teach(client, applicant)
    finished = _finish(client, applicant, session_id)
    assert finished.status_code == 200, finished.text
    body = finished.json()
    assert body["candidate_id"] == "c-003"
    assert body["overall_score"] == 72
    assert body["message_count"] == 4
    assert [a["confident"] for a in body["quiz_answers"]] == [True, True, False]

    # A new engine on the same file stands in for a restarted server.
    db.dispose()
    restarted = make_engine(str(db.url))
    set_engine(restarted)
    try:
        _check_stored(client, restarted, session_id, body, auth_headers("committee"))
    finally:
        restarted.dispose()


def _check_stored(client, db, session_id, body, committee):
    row = _row(db, session_id)
    assert row.status == "finished"
    assert row.finished_at is not None
    assert row.applicant_id == applicant_id_for("c-003")
    # Opening turn plus three exchanges, both sides of each.
    assert len(row.messages) == 8
    assert row.messages[2] == {"role": "user", "content": "The Earth is tilted."}

    stored = client.get("/api/feynman/score/c-003", headers=committee).json()
    assert stored["session_id"] == session_id
    assert stored["topic_id"] == "seasons"
    assert stored["summary"] == SCORE["summary"]
    assert stored["quiz_answers"] == body["quiz_answers"]
    with Session(db) as session:
        assert session.exec(select(FeynmanScoreRecord.model)).one() == settings.MODEL_JUDGE


def test_score_is_null_before_any_attempt(client, auth_headers):
    assert client.get("/api/feynman/score/c-003", headers=auth_headers("committee")).json() is None


def test_latest_attempt_is_the_score_shown(client, model, applicant, monkeypatch):
    first = _teach(client, applicant)
    _finish(client, applicant, first)
    monkeypatch.setitem(SCORE, "overall_score", 90)
    second = _teach(client, applicant)
    _finish(client, applicant, second)

    shown = client.get("/api/feynman/score/c-003", headers=applicant).json()
    assert (shown["session_id"], shown["overall_score"]) == (second, 90)


def test_finished_session_is_closed(client, model, applicant):
    session_id = _teach(client, applicant)
    assert _finish(client, applicant, session_id).status_code == 200
    assert _chat(client, applicant, session_id).status_code == 409
    assert _finish(client, applicant, session_id).status_code == 409
    assert model.json_calls == 2  # quiz and scorer, once


def test_session_deleted_with_its_applicant_account(client, db, model, applicant):
    session_id = _start(client, applicant).json()["session_id"]
    user_id = _row(db, session_id).user_id
    with Session(db) as session:
        session.delete(session.get(User, user_id))
        session.commit()
    assert _row(db, session_id) is None


# ── Attempt limit ──────────────────────────────────────────────────


def test_attempt_limit_is_enforced_before_the_model_is_called(client, model, applicant, monkeypatch):
    monkeypatch.setattr(settings, "FEYNMAN_MAX_ATTEMPTS", 2)
    assert _start(client, applicant).status_code == 200
    assert _start(client, applicant, topic="rain").status_code == 200

    third = _start(client, applicant, topic="gravity")
    assert third.status_code == 429
    assert "2 attempts" in third.json()["detail"]
    assert third.headers["access-control-allow-origin"] == ORIGIN
    assert model.chat_calls == 2


def test_attempts_are_per_applicant(client, model, applicant, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "FEYNMAN_MAX_ATTEMPTS", 1)
    assert _start(client, applicant).status_code == 200
    other = auth_headers("applicant", owns="c-004")
    response = client.post("/api/feynman/start", json={"candidate_id": "c-004", "topic_id": "rain"}, headers=other)
    assert response.status_code == 200


def test_starting_again_abandons_the_open_attempt(client, db, model, applicant):
    first = _start(client, applicant).json()["session_id"]
    _start(client, applicant, topic="rain")
    assert _row(db, first).status == "abandoned"
    assert _chat(client, applicant, first).status_code == 409


def test_last_attempt_cannot_be_taken_twice(client, db, applicant):
    """The race the pre-check cannot close: two starts that both passed it."""
    user_id = client.get("/api/auth/me", headers=applicant).json()["id"]
    applicant_id = applicant_id_for("c-003")

    assert store.create_session(applicant_id, user_id, "seasons", [], max_attempts=1) is not None
    assert store.create_session(applicant_id, user_id, "seasons", [], max_attempts=1) is None
    with Session(db) as session:
        assert session.exec(select(func.count()).select_from(FeynmanSession)).one() == 1


# ── Model failures ─────────────────────────────────────────────────


def test_failed_start_is_a_readable_error_and_costs_no_attempt(client, db, model, applicant, monkeypatch):
    monkeypatch.setattr(settings, "FEYNMAN_MAX_ATTEMPTS", 1)
    model.fail = _connection_error()
    response = _start(client, applicant)
    assert response.status_code == 502
    assert response.json()["detail"] == "The AI student could not answer right now. Please try again."
    # The browser can read it: this was a CORS-less 500 ("Failed to fetch").
    assert response.headers["access-control-allow-origin"] == ORIGIN
    with Session(db) as session:
        assert session.exec(select(func.count()).select_from(FeynmanSession)).one() == 0

    model.fail = None
    assert _start(client, applicant).status_code == 200


def test_failed_chat_leaves_the_session_unchanged(client, db, model, applicant):
    session_id = _start(client, applicant).json()["session_id"]
    model.fail = _connection_error()
    response = _chat(client, applicant, session_id)
    assert response.status_code == 502
    assert response.headers["access-control-allow-origin"] == ORIGIN
    row = _row(db, session_id)
    assert (row.exchange_count, len(row.messages)) == (1, 2)

    model.fail = None
    retried = _chat(client, applicant, session_id)
    assert retried.status_code == 200
    assert retried.json()["message_count"] == 2


def test_rate_limit_is_503(client, model, applicant):
    model.fail = _rate_limit_error()
    response = _start(client, applicant)
    assert response.status_code == 503
    assert response.headers["access-control-allow-origin"] == ORIGIN


def test_failed_finish_reopens_the_session_for_a_retry(client, db, model, applicant):
    session_id = _teach(client, applicant)
    model.fail = ValueError("model reply contained no text block")
    response = _finish(client, applicant, session_id)
    assert response.status_code == 502
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert _row(db, session_id).status == "active"

    model.fail = None
    assert _finish(client, applicant, session_id).status_code == 200


def test_finish_while_scoring_is_refused(client, model, applicant):
    session_id = _teach(client, applicant)
    assert store.claim_for_scoring(session_id)
    assert _finish(client, applicant, session_id).status_code == 409
    assert model.json_calls == 0


def test_a_stale_turn_does_not_overwrite_a_newer_one(client, db, model, applicant):
    """Two sends of the same turn: the second must not replace the first."""
    session_id = _start(client, applicant).json()["session_id"]
    assert _chat(client, applicant, session_id).status_code == 200
    assert not store.record_exchange(session_id, 1, [{"role": "user", "content": "stale"}])
    assert _row(db, session_id).exchange_count == 2
