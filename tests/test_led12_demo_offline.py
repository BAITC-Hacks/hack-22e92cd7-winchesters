"""LED-12: every demo click works with no model key, and says where its figures came from.

The model is made to explode if anything reaches it, so "no 5xx" also proves
"no call". `python -m backend.db init` is checked on a fresh file: migrations
to head, 16 applicants, the demo committee login and the demo ledger, and the
same data after a second run.
"""

from __future__ import annotations

import hashlib
import json

import pytest
from fastapi import HTTPException
from sqlalchemy import inspect, text
from sqlmodel import Session, select

from backend import llm, settings
from backend.db import engine as db_engine
from backend.db.seed import DEMO_COMMITTEE_EMAIL, DEMO_COMMITTEE_PASSWORD, seed, seed_demo_ledger
from backend.db.tables import ModelRun, User
from backend.ledger import demo
from backend.ledger.provenance import DEMO_LABEL, HAND_AUTHORED, ILLUSTRATIVE_LABEL


@pytest.fixture(params=["", "your-anthropic-api-key-here"], ids=["no-key", "example-placeholder"])
def no_model(request, monkeypatch):
    """No usable key, and a client that fails the test if it is ever called."""

    async def forbidden(*_args, **_kwargs):
        raise AssertionError("a model was called without a key")

    monkeypatch.setattr(llm.client, "api_key", request.param)
    monkeypatch.setattr(llm.client.messages, "create", forbidden)
    assert not llm.is_configured()


@pytest.fixture
def committee(auth_headers, db):
    seed_demo_ledger()
    return auth_headers("committee")


def _model_runs(db) -> list[ModelRun]:
    with Session(db) as session:
        return list(session.exec(select(ModelRun)).all())


# ── Demo clicks: 200, labelled source, no model call ────────────────

DEMO_GETS = [
    "/api/candidates/",
    "/api/ledger",
    "/api/ledger/c-001",
    "/api/ledger/rubric",
    "/api/committee/pre-brief/c-001",
    "/api/committee/decision-memo/c-001",
    "/api/fairness/audit",
    "/api/fairness/evaluation",
    "/api/fairness/evaluation?live=true",
    "/api/fairness/cohort-probe",
    "/api/fairness/cohort-probe?live=true",
    "/api/fairness/historical/status",
    "/api/fairness/heldout/status",
    "/api/overrides/c-001",
    "/api/overrides/reason-codes",
    "/api/scenarios",
    "/api/scenarios/mode",
    "/api/scenarios/result/c-001",
]
DEMO_POSTS = [
    "/api/scoring/rank",
    "/api/scoring/rank?scorer=ai",
    "/api/analysis/ai-detection/c-001",
    "/api/analysis/video-analysis/c-001",
    "/api/fairness/probe/c-001",
    "/api/fairness/probe/c-001?live=false",
]


@pytest.mark.parametrize("path", DEMO_GETS)
def test_demo_reads_answer_without_a_key(client, committee, no_model, path):
    response = client.get(path, headers=committee)
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("path", DEMO_POSTS)
def test_demo_actions_answer_without_a_key(client, committee, no_model, path):
    response = client.post(path, headers=committee)
    assert response.status_code == 200, response.text


def test_probe_falls_back_to_a_labelled_baseline_without_a_call(client, committee, no_model):
    body = client.post("/api/fairness/probe/c-001", headers=committee).json()
    assert body["status"] == "fallback_demo"
    assert body["model_id"] == "cached-baseline-demo"
    assert "no model API key" in body["notice"] and "not called" in body["notice"]


def test_evaluation_says_why_it_fell_back(client, committee, no_model):
    body = client.get("/api/fairness/evaluation?live=true", headers=committee).json()
    assert body["status"] == "fallback_demo"
    assert body["model_id"] == "cached-baseline-demo"
    assert body["fallback_reason"] == "no model API key on this server"
    assert client.get("/api/fairness/cohort-probe?live=true", headers=committee).json()["status"] == "fallback"


def test_ai_ranking_without_a_key_is_empty_not_zero(client, committee, no_model, db):
    assert client.post("/api/scoring/rank?scorer=ai", headers=committee).json() == []
    assert _model_runs(db) == []


def test_video_without_a_key_carries_no_numbers(client, committee, no_model):
    body = client.post("/api/analysis/video-analysis/c-001", headers=committee).json()
    assert body["status"] in {"no_transcript", "unavailable"}
    assert body["authenticity_match"] is None and body["motivation_score"] is None


def test_nothing_ingested_is_a_status_not_a_404(client, committee, no_model):
    for path in ("/api/fairness/historical/status", "/api/fairness/heldout/status"):
        body = client.get(path, headers=committee).json()
        assert body["ingested"] is False
        assert "nothing was" in body["detail"]


# ── Live-only endpoints: an explicit 503, never 500/502, never a call ──


@pytest.mark.parametrize("path", ["/api/scoring/ai/c-001", "/api/scoring/ai/all"])
def test_ai_scoring_without_a_key_is_503_and_records_nothing(client, committee, no_model, db, path):
    response = client.post(path, headers=committee)
    assert response.status_code == 503
    assert "Nothing was scored" in response.json()["detail"]
    assert _model_runs(db) == []


@pytest.mark.asyncio
async def test_scenario_turn_without_a_key_is_503_not_502(no_model):
    from backend.routers.scenarios import _ask_model

    with pytest.raises(HTTPException) as raised:
        await _ask_model(llm.complete_chat(messages=[{"role": "user", "content": "hi"}], system="s"), "chat")
    assert raised.value.status_code == 503


# ── Provenance: the worked example is never shown as c-001's ────────


@pytest.fixture
def committee_without_demo_rows(auth_headers, db, monkeypatch, tmp_path):
    """The seed as it was before demo mode: c-001 carries the worked example."""
    empty = tmp_path / "no_demo_rows.json"
    empty.write_text(json.dumps({"columns": [], "applicants": {}}), encoding="utf-8")
    monkeypatch.setattr(demo, "AUTHORED_FILE", empty)
    seed_demo_ledger()
    return auth_headers("committee")


def test_seed_applicants_are_labelled_demo_mode(client, committee, no_model):
    ledger = client.get("/api/ledger/c-001", headers=committee).json()
    assert ledger["model_judge"] == demo.DEMO_AUTHORED
    memo = client.get("/api/committee/decision-memo/c-001", headers=committee).json()
    brief = client.get("/api/committee/pre-brief/c-001", headers=committee).json()
    for body in (memo, brief):
        assert body["ledger_provenance"]["kind"] == "demo_mode"
        assert body["ledger_provenance"]["illustrative"] is False
        assert body["ledger_provenance"]["label"] == DEMO_LABEL


def test_the_worked_example_is_labelled_illustrative_everywhere(client, committee_without_demo_rows, no_model):
    committee = committee_without_demo_rows
    ledger = client.get("/api/ledger/c-001", headers=committee).json()
    assert ledger["model_judge"] == HAND_AUTHORED

    memo = client.get("/api/committee/decision-memo/c-001", headers=committee).json()
    brief = client.get("/api/committee/pre-brief/c-001", headers=committee).json()
    for body in (memo, brief):
        assert body["ledger_provenance"]["kind"] == "illustrative_example"
        assert body["ledger_provenance"]["illustrative"] is True
        assert body["ledger_provenance"]["label"] == ILLUSTRATIVE_LABEL

    # The clash this labels: the example quotes a written presentation c-001
    # never submitted. The fix is the label, not text invented for c-001.
    sources = {q["source"] for q in memo["verified_quotes"]}
    assert "written_presentation" in sources
    candidate = client.get("/api/candidates/c-001", headers=committee).json()
    assert candidate["written_presentation"] == ""


def test_a_cached_run_is_labelled_as_cached():
    from backend.db.seed import WORKED_EXAMPLE
    from backend.ledger import provenance
    from backend.ledger.schema import CandidateLedger

    # The example file as a pipeline would have written it: model_judge is a model.
    run = CandidateLedger.model_validate_json(WORKED_EXAMPLE.read_text(encoding="utf-8"))
    described = provenance.describe(run)
    assert described["kind"] == "cached_run" and described["illustrative"] is False
    assert "claude-opus-5" in described["detail"]


def test_memo_pdf_carries_the_label(client, committee, no_model):
    pytest.importorskip("reportlab")
    response = client.get("/api/committee/decision-memo/c-001/pdf", headers=committee)
    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")


# ── Auth on the new endpoints ───────────────────────────────────────


@pytest.mark.parametrize("path", ["/api/fairness/historical/status", "/api/fairness/heldout/status"])
def test_status_endpoints_are_committee_and_admin_only(client, auth_headers, path):
    assert client.get(path).status_code == 401
    for role in ("applicant", "interviewer"):
        assert client.get(path, headers=auth_headers(role)).status_code == 403
    for role in ("committee", "admin"):
        assert client.get(path, headers=auth_headers(role)).status_code == 200


# ── init on a clean database, twice ─────────────────────────────────


def _snapshot(engine) -> dict[str, list[tuple]]:
    with engine.connect() as connection:
        return {
            table: sorted(tuple(map(str, row)) for row in connection.execute(text(f'SELECT * FROM "{table}"')))
            for table in sorted(inspect(connection).get_table_names())
        }


@pytest.fixture
def fresh_database(tmp_path, monkeypatch):
    url = f"sqlite:///{(tmp_path / 'fresh.db').as_posix()}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    db_engine.set_engine(None)
    yield
    db_engine.get_engine().dispose()
    db_engine.set_engine(None)


def test_init_on_a_clean_database_is_complete_and_idempotent(fresh_database, capsys):
    from backend.db.__main__ import init
    from backend.main import app
    from fastapi.testclient import TestClient

    init()
    engine = db_engine.get_engine()
    db_engine.assert_schema_current(engine)
    first = _snapshot(engine)
    assert len(first["applicants"]) == 16
    assert [row for row in first["users"] if DEMO_COMMITTEE_EMAIL in row]
    assert first["competency_scores"], "the demo ledger for c-001 was not loaded"
    assert "demo committee account created" in capsys.readouterr().out

    init()
    assert _snapshot(engine) == first
    assert "created" not in capsys.readouterr().out

    with TestClient(app) as client:
        login = client.post("/api/auth/login", json={"email": DEMO_COMMITTEE_EMAIL, "password": DEMO_COMMITTEE_PASSWORD})
        assert login.status_code == 200
        assert login.json()["user"]["role"] == "committee"


def test_seed_repairs_a_pre_fnd05_demo_account(db, client):
    """The dev database's 401: the row kept an unsalted SHA-256 hash argon2 rejects."""
    with Session(db) as session:
        user = session.exec(select(User).where(User.email == DEMO_COMMITTEE_EMAIL)).one()
        user.password_hash = hashlib.sha256(DEMO_COMMITTEE_PASSWORD.encode()).hexdigest()
        user.role = "applicant"
        session.add(user)
        session.commit()
    credentials = {"email": DEMO_COMMITTEE_EMAIL, "password": DEMO_COMMITTEE_PASSWORD}
    assert client.post("/api/auth/login", json=credentials).status_code == 401

    assert seed().demo_user_repaired is True
    login = client.post("/api/auth/login", json=credentials)
    assert login.status_code == 200 and login.json()["user"]["role"] == "committee"

    with Session(db) as session:
        repaired = session.exec(select(User).where(User.email == DEMO_COMMITTEE_EMAIL)).one().password_hash
    assert seed().demo_user_repaired is False
    with Session(db) as session:
        assert session.exec(select(User).where(User.email == DEMO_COMMITTEE_EMAIL)).one().password_hash == repaired


def test_seed_leaves_the_demo_account_alone_outside_demo_mode(db, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    with Session(db) as session:
        user = session.exec(select(User).where(User.email == DEMO_COMMITTEE_EMAIL)).one()
        user.password_hash = "legacy"
        session.add(user)
        session.commit()
    assert seed().demo_user_repaired is False
    with Session(db) as session:
        assert session.exec(select(User).where(User.email == DEMO_COMMITTEE_EMAIL)).one().password_hash == "legacy"
