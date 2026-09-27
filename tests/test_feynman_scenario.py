"""INP-03, Scenario Lab half: the Teamwork fork, the cached demo, weight zero.

What these pin: the scenario runs on the Feynman mechanism with its own
prompts and is marked provisional, never approved; without a model key the
live start is refused before an attempt is spent and the cached demo
transcript is served, labelled as cached; a simulation result carries weight
zero and the label "observed in simulation", and storing one moves no score
and no rank; the new endpoints are behind auth. Offline: no model is called.
"""

from __future__ import annotations

import ast
import json
import pathlib

import pytest
from sqlalchemy import func
from sqlmodel import Session, select

from backend import llm
from backend.db import feynman as store
from backend.db.candidates import applicant_id_for
from backend.db.tables import FeynmanSession
from backend.models import ScoringWeights
from backend.routers import feynman

from tests.test_feynman import SCORE, FakeModel, _chat, _finish, _start

ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture
def applicant(auth_headers) -> dict[str, str]:
    return auth_headers("applicant", owns="c-003")


@pytest.fixture
def live_model(monkeypatch) -> FakeModel:
    fake = FakeModel()
    monkeypatch.setattr(llm, "complete_chat", fake.complete_chat)
    monkeypatch.setattr(llm, "complete_json", fake.complete_json)
    monkeypatch.setattr(llm, "is_configured", lambda: True)
    return fake


@pytest.fixture
def no_key(monkeypatch) -> FakeModel:
    """No API key on the server. The fake would still answer, to prove it is never asked."""
    fake = FakeModel()
    monkeypatch.setattr(llm, "complete_chat", fake.complete_chat)
    monkeypatch.setattr(llm, "complete_json", fake.complete_json)
    monkeypatch.setattr(llm, "is_configured", lambda: False)
    return fake


# ── The fork ───────────────────────────────────────────────────────


def test_scenario_is_listed_as_a_provisional_teamwork_fork(client, applicant):
    topics = client.get("/api/feynman/topics", headers=applicant).json()
    scenario = next(t for t in topics if t["id"] == feynman.SCENARIO_ID)
    assert scenario["kind"] == "scenario"
    assert scenario["competency"] == "teamwork"
    assert scenario["status"] == "provisional"
    assert "Talent Craft" in scenario["status_note"]
    assert {t["kind"] for t in topics if t["id"] != feynman.SCENARIO_ID} == {"teaching"}


def test_no_approval_claim_anywhere_in_the_scenario():
    text = json.dumps(feynman.SCENARIO_TOPIC) + feynman.SCENARIO_SYSTEM_PROMPT + feynman.SCENARIO_SCORER_PROMPT
    for word in ("approved", "frozen", "verified", "validated"):
        assert word not in text.lower()


def test_scenario_hash_follows_the_wording_not_a_label(monkeypatch):
    before = feynman.scenario_content_hash()
    assert before == feynman.SCENARIO_TOPIC["content_hash"]
    monkeypatch.setattr(feynman, "SCENARIO_STATUS", "anything")
    assert feynman.scenario_content_hash() == before
    monkeypatch.setattr(feynman, "SCENARIO_SITUATION", feynman.SCENARIO_SITUATION + " ")
    assert feynman.scenario_content_hash() != before


class RecordingModel(FakeModel):
    def __init__(self) -> None:
        super().__init__()
        self.systems: list[str] = []
        self.prompts: list[str] = []

    async def complete_chat(self, messages, system, model=""):
        self.systems.append(system)
        return await super().complete_chat(messages, system, model)

    async def complete_json(self, prompt, schema, system="", model=""):
        self.systems.append(system)
        self.prompts.append(prompt)
        return await super().complete_json(prompt, schema, system, model)


def test_scenario_session_uses_the_scenario_prompts(client, applicant, monkeypatch):
    model = RecordingModel()
    monkeypatch.setattr(llm, "complete_chat", model.complete_chat)
    monkeypatch.setattr(llm, "complete_json", model.complete_json)
    monkeypatch.setattr(llm, "is_configured", lambda: True)

    session_id = _start(client, applicant, topic=feynman.SCENARIO_ID).json()["session_id"]
    for _ in range(3):
        assert _chat(client, applicant, session_id, "I would talk to Dana first.").status_code == 200
    body = _finish(client, applicant, session_id).json()

    assert all(feynman.SCENARIO_SITUATION in system for system in model.systems[:4])
    quiz_prompt, scorer_prompt = model.prompts
    assert "What did they say you should do about Dana?" in quiz_prompt
    assert '<document source="lesson"' in quiz_prompt
    assert "There is no correct choice" in scorer_prompt
    assert '<document source="scenario_session"' in scorer_prompt
    assert (body["kind"], body["weight"], body["label"], body["source"]) == (
        "scenario", 0.0, "observed in simulation", "live",
    )


# ── Cached demo, no key ────────────────────────────────────────────


def test_mode_reports_live_only_with_a_key(client, applicant, monkeypatch):
    monkeypatch.setattr(llm, "is_configured", lambda: False)
    mode = client.get("/api/feynman/mode", headers=applicant).json()
    assert mode["live"] is False and "key" in mode["reason"]
    assert mode["cached_label"] == "cached demo transcript"
    monkeypatch.setattr(llm, "is_configured", lambda: True)
    assert client.get("/api/feynman/mode", headers=applicant).json()["live"] is True


def test_without_a_key_start_is_refused_before_any_attempt_or_call(client, db, applicant, no_key):
    for topic in (feynman.SCENARIO_ID, "seasons"):
        response = _start(client, applicant, topic=topic)
        assert response.status_code == 503
        assert "cached demo transcript" in response.json()["detail"]
    assert no_key.chat_calls == 0
    assert store.attempts_used(applicant_id_for("c-003")) == 0
    with Session(db) as session:
        assert session.exec(select(func.count()).select_from(FeynmanSession)).one() == 0


def test_cached_demo_is_served_without_a_key_and_says_so(client, applicant, no_key):
    response = client.get("/api/feynman/demo", headers=applicant)
    assert response.status_code == 200
    demo = response.json()
    assert (demo["source"], demo["label"]) == ("cached_demo", "cached demo transcript")
    assert "Not generated by a model" in demo["provenance"]
    assert demo["topic"]["id"] == feynman.SCENARIO_ID
    score = demo["score"]
    assert (score["source"], score["weight"], score["label"], score["kind"]) == (
        "cached_demo", 0.0, "observed in simulation", "scenario",
    )
    # Never attributed to a real candidate.
    assert score["candidate_id"] == "" and score["session_id"] == "cached-demo"
    assert no_key.chat_calls == no_key.json_calls == 0


def test_cached_transcript_is_a_complete_valid_session():
    raw = json.loads(feynman.DEMO_TRANSCRIPT_PATH.read_text(encoding="utf-8"))
    messages = raw["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant"] * (len(messages) // 2)
    exchanges = len(messages) // 2
    assert feynman.MIN_EXCHANGES_TO_FINISH <= exchanges <= feynman.MAX_EXCHANGES
    assert messages[0]["content"] == feynman._opening(feynman.SCENARIO_TOPIC)
    questions = [a["question"] for a in raw["score"]["quiz_answers"]]
    assert questions == feynman.QUIZ_QUESTIONS[feynman.SCENARIO_ID]
    assert set(raw["score"]) >= set(feynman.TEACHING_SCHEMA["required"])
    assert "weight" not in raw["score"] and "source" not in raw["score"]


def test_cached_demo_is_never_stored_as_a_score(client, applicant, auth_headers, no_key):
    client.get("/api/feynman/demo", headers=applicant)
    assert client.get("/api/feynman/score/c-003", headers=auth_headers("committee")).json() is None


# ── Weight zero ────────────────────────────────────────────────────


def _rankings(client, committee) -> dict:
    return {
        scorer: client.post(f"/api/scoring/rank?scorer={scorer}", headers=committee).json()
        for scorer in ("baseline", "ai")
    } | {"c-003": client.post("/api/scoring/baseline/c-003", headers=committee).json()}


def test_a_simulation_result_moves_no_score_and_no_rank(client, auth_headers, applicant, live_model, monkeypatch):
    committee = auth_headers("committee")
    before = _rankings(client, committee)

    # The strongest possible simulation result, for a mid-table candidate.
    for key in ("clarity", "patience", "empathy", "adaptability", "quiz_transfer_score", "overall_score"):
        monkeypatch.setitem(SCORE, key, 100)
    session_id = _start(client, applicant, topic=feynman.SCENARIO_ID).json()["session_id"]
    for _ in range(3):
        _chat(client, applicant, session_id)
    assert _finish(client, applicant, session_id).json()["overall_score"] == 100

    assert _rankings(client, committee) == before


def test_weight_is_zero_and_every_result_is_labelled(client, auth_headers, applicant, live_model):
    assert feynman.SIMULATION_WEIGHT == 0
    assert feynman.SIMULATION_LABEL == "observed in simulation"
    session_id = _start(client, applicant).json()["session_id"]
    for _ in range(3):
        _chat(client, applicant, session_id)
    finished = _finish(client, applicant, session_id).json()
    stored = client.get("/api/feynman/score/c-003", headers=auth_headers("committee")).json()
    for body in (finished, stored):
        assert (body["weight"], body["label"]) == (0.0, "observed in simulation")


def test_scoring_weights_have_no_simulation_term():
    for field in ScoringWeights.model_fields:
        assert not any(word in field for word in ("feynman", "teach", "simulation", "scenario"))


# Modules that may know simulations exist. Anything else importing them is a
# path by which a simulation result could reach a score.
SIMULATION_AWARE = {
    "backend/routers/feynman.py",
    "backend/db/feynman.py",
    "backend/db/tables.py",
    "backend/main.py",
}


def _imported_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module or "")
            names.update(alias.name for alias in node.names)
    return names


def test_no_scoring_path_imports_the_simulation():
    offenders = []
    for path in sorted((ROOT / "backend").rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if rel in SIMULATION_AWARE or rel.startswith("backend/migrations/"):
            continue
        names = _imported_names(ast.parse(path.read_text(encoding="utf-8")))
        if any("feynman" in name.lower() for name in names):
            offenders.append(rel)
    assert offenders == []


# ── Authorization ──────────────────────────────────────────────────


@pytest.mark.parametrize("path", ["/api/feynman/mode", "/api/feynman/demo", "/api/feynman/topics"])
def test_simulation_endpoints_need_a_login(client, path):
    assert client.get(path).status_code == 401


def test_staff_can_read_the_demo_but_not_start_a_scenario(client, auth_headers, live_model):
    committee = auth_headers("committee")
    assert client.get("/api/feynman/demo", headers=committee).status_code == 200
    assert _start(client, committee, topic=feynman.SCENARIO_ID).status_code == 403
    assert live_model.chat_calls == 0


def test_applicant_cannot_start_a_scenario_for_someone_else(client, applicant, live_model):
    response = client.post(
        "/api/feynman/start", json={"candidate_id": "c-004", "topic_id": feynman.SCENARIO_ID}, headers=applicant
    )
    assert response.status_code == 403
    assert live_model.chat_calls == 0


def test_applicant_cannot_read_another_scenario_session(client, auth_headers, applicant, live_model):
    session_id = _start(client, applicant, topic=feynman.SCENARIO_ID).json()["session_id"]
    other = auth_headers("applicant", owns="c-004")
    assert _chat(client, other, session_id).status_code == 404
    assert _finish(client, other, session_id).status_code == 404
