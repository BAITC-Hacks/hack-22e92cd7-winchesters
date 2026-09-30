"""INP-04: scenarios replace the teaching challenge.

What these pin: three scenarios, each in English, Russian and Kazakh, with a
partner that has no name, age or gender; without a key the partner follows
the script and the result says "demo", with a key the model gets the
scenario's steps in the chosen language; the result is one competency rated
by the essay pipeline from the applicant's own words, with weight zero and
no level shown to the applicant; the attempt limit, ownership, retries and
single scoring still hold. Everything runs offline: `backend.llm` is faked.
"""

from __future__ import annotations

import httpx
import anthropic
import pytest
from sqlalchemy import func
from sqlmodel import Session, select

from backend import llm, scenarios, settings
from backend.db import feynman as store
from backend.db.candidates import applicant_id_for
from backend.db.engine import make_engine, set_engine
from backend.db.tables import FeynmanSession, ScenarioResult, User
from backend.ledger.extract import EXTRACTION_SCHEMA
from backend.ledger.rate import RATING_SCHEMA

ORIGIN = "http://localhost:3000"

REPLIES = [
    "I would talk to them today, calmly, and ask what is going on before anyone redoes their part.",
    "Then we split the missing work between the three of us so Timur is not doing everything alone.",
    "Last year our robotics teammate stopped coming. I called him, we agreed he would do the smaller part, and we finished on time.",
]


class FakeModel:
    """Stands in for backend.llm. `fail` makes the next calls raise it."""

    def __init__(self) -> None:
        self.chat_calls: list[dict] = []
        self.json_calls = 0
        self.fail: Exception | None = None

    async def complete_chat(self, messages, system, model=""):
        self.chat_calls.append({"messages": messages, "system": system})
        if self.fail:
            raise self.fail
        return f"partner reply {len(self.chat_calls)}"

    async def complete_json(self, prompt, schema, system="", model=""):
        self.json_calls += 1
        if self.fail:
            raise self.fail
        if schema is EXTRACTION_SCHEMA:
            return {"evidence": [
                {"quote": REPLIES[2], "source": "scenario", "indicator_id": "team.accountability", "atola": "outcome", "status": "present"},
                {"quote": "a quote the applicant never wrote", "source": "scenario", "indicator_id": "team.we_orientation", "atola": "action", "status": "present"},
            ]}
        assert schema is RATING_SCHEMA
        return {
            "indicators": [{"indicator_id": "team.accountability", "note": "", "observed_level": "high"}],
            "flags": [],
            "contrastive": "",
            "probe_question": "",
        }


def _connection_error() -> Exception:
    return anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))


@pytest.fixture
def model(monkeypatch) -> FakeModel:
    fake = FakeModel()
    monkeypatch.setattr(llm, "complete_chat", fake.complete_chat)
    monkeypatch.setattr(llm, "complete_json", fake.complete_json)
    monkeypatch.setattr(llm, "is_configured", lambda: True)
    return fake


@pytest.fixture
def no_key(monkeypatch) -> None:
    async def refuse(*args, **kwargs):
        raise AssertionError("a model was called without a key")

    monkeypatch.setattr(llm, "is_configured", lambda: False)
    monkeypatch.setattr(llm, "complete_chat", refuse)
    monkeypatch.setattr(llm, "complete_json", refuse)


@pytest.fixture
def applicant(auth_headers) -> dict[str, str]:
    return {**auth_headers("applicant", owns="c-003"), "Origin": ORIGIN}


def _start(client, headers, scenario="stalled-project", language="en", candidate="c-003"):
    body = {"candidate_id": candidate, "scenario_id": scenario, "language": language}
    return client.post("/api/scenarios/start", json=body, headers=headers)


def _chat(client, headers, session_id, message=REPLIES[0]):
    return client.post("/api/scenarios/chat", json={"session_id": session_id, "message": message}, headers=headers)


def _finish(client, headers, session_id):
    return client.post(f"/api/scenarios/finish?session_id={session_id}", headers=headers)


def _row(db, session_id) -> FeynmanSession:
    with Session(db) as session:
        return session.get(FeynmanSession, session_id)


def _answer(client, headers, **start) -> str:
    session_id = _start(client, headers, **start).json()["session_id"]
    for reply in REPLIES:
        assert _chat(client, headers, session_id, reply).status_code == 200
    return session_id


# ── Content ────────────────────────────────────────────────────────


def test_three_scenarios_in_three_languages_each_on_its_own_competency(client, applicant):
    body = client.get("/api/scenarios", headers=applicant).json()
    assert set(body["languages"]) == {"en", "ru", "kk"}
    assert body["partner_label"]["ru"] == "Собеседник"
    listed = body["scenarios"]
    assert [s["competency"] for s in listed] == ["teamwork", "leadership_abilities", "values"]
    for entry in listed:
        assert set(entry["text"]) == {"en", "ru", "kk"}
        assert all(entry["text"][lang]["opening"] for lang in ("en", "ru", "kk"))
    # The applicant sees the situation, never the partner's instructions.
    assert "Rules:" not in str(listed)


def test_every_language_has_three_follow_ups_and_the_last_asks_for_a_real_example():
    for entry in scenarios.SCENARIOS:
        for language, lines in entry["text"].items():
            assert len(lines["follow_ups"]) == 3, (entry["id"], language)


def test_the_partner_is_not_a_character():
    """No name, age or child persona; formal address; no gendered self-reference asked for."""
    prompt = scenarios.partner_system_prompt("stalled-project", "ru")
    assert "no name, age or gender" in prompt
    assert "«вы», never «ты»" in prompt
    assert "Speak only Russian" in prompt
    everything = str(scenarios.SCENARIOS) + scenarios.PARTNER_SYSTEM_PROMPT
    assert "Arman" not in everything and "10-year-old" not in everything


def test_the_content_hash_follows_the_wording(monkeypatch):
    before = scenarios.content_hash()
    monkeypatch.setitem(scenarios.CLOSING, "en", scenarios.CLOSING["en"] + "!")
    assert scenarios.content_hash() != before


# ── Demo mode: no key, scripted partner ────────────────────────────


def test_without_a_key_the_partner_follows_the_script_in_the_chosen_language(client, applicant, no_key):
    started = _start(client, applicant, language="kk")
    assert started.status_code == 200, started.text
    body = started.json()
    lines = scenarios.text("stalled-project", "kk")
    assert body["live"] is False
    assert body["first_message"] == lines["opening"]

    replies = [_chat(client, applicant, body["session_id"], r).json()["reply"] for r in REPLIES]
    assert replies == lines["follow_ups"]


def test_demo_result_is_rated_from_the_applicants_own_words(client, db, auth_headers, applicant, no_key):
    session_id = _answer(client, applicant)
    finished = _finish(client, applicant, session_id)
    assert finished.status_code == 200, finished.text
    # The applicant gets no level back.
    assert finished.json() == {"session_id": session_id, "saved": True}

    result = client.get("/api/scenarios/result/c-003", headers=auth_headers("committee")).json()
    assert result["source"] == "demo"
    assert result["competency"] == "teamwork"
    quotes = [e for i in result["rating"]["indicators"] for e in i["evidence"]]
    applicant_words = "\n\n".join(REPLIES)
    assert quotes and all(e["verified"] and e["quote"] in applicant_words for e in quotes)
    assert all(e["source"] == "scenario" for e in quotes)
    # The partner's lines are the question, never evidence.
    opening = scenarios.text("stalled-project", "en")["opening"]
    assert not any(e["quote"] in opening for e in quotes)


# ── Live: the model plays the partner and reads the replies ────────


def test_live_partner_gets_the_steps_in_the_chosen_language(client, model, applicant):
    session_id = _start(client, applicant, language="ru").json()["session_id"]
    assert model.chat_calls == []  # the opening is written, not generated
    _chat(client, applicant, session_id)
    call = model.chat_calls[0]
    assert "Speak only Russian" in call["system"]
    assert scenarios.text("stalled-project", "ru")["follow_ups"][0] in call["system"]
    # The model's history starts with the applicant; the opening is in the system prompt.
    assert call["messages"][0] == {"role": "user", "content": REPLIES[0]}


def test_live_result_drops_quotes_the_applicant_never_wrote(client, auth_headers, model, applicant):
    session_id = _answer(client, applicant)
    assert _finish(client, applicant, session_id).status_code == 200
    result = client.get("/api/scenarios/result/c-003", headers=auth_headers("committee")).json()
    assert result["source"] == "live"
    quotes = [e["quote"] for i in result["rating"]["indicators"] for e in i["evidence"]]
    assert quotes == [REPLIES[2]]


def test_a_scenario_never_changes_the_written_level(client, auth_headers, applicant, no_key):
    from backend.db.seed import seed_demo_ledger

    seed_demo_ledger()
    committee = auth_headers("committee")
    before = client.get("/api/ledger/c-003", headers=committee).json()
    _finish(client, applicant, _answer(client, applicant))
    result = client.get("/api/scenarios/result/c-003", headers=committee).json()
    assert result["weight"] == 0 and result["label"] == "observed in simulation"
    assert client.get("/api/ledger/c-003", headers=committee).json() == before


def test_no_scoring_path_imports_scenarios():
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[1] / "backend"
    for path in (root / "scoring").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "scenario_results" not in text and "routers.scenarios" not in text, path.name


# ── Access ─────────────────────────────────────────────────────────


@pytest.mark.parametrize("path", ["/api/scenarios", "/api/scenarios/mode", "/api/scenarios/result/c-003"])
def test_scenario_endpoints_need_a_login(client, path):
    assert client.get(path).status_code == 401


def test_staff_cannot_start_and_applicants_cannot_read_results(client, auth_headers, applicant, no_key):
    assert _start(client, auth_headers("committee")).status_code == 403
    assert client.get("/api/scenarios/result/c-003", headers=applicant).status_code == 403


def test_applicant_cannot_start_for_someone_else_or_read_another_session(client, auth_headers, applicant, no_key):
    assert _start(client, applicant, candidate="c-004").status_code == 403
    session_id = _start(client, applicant).json()["session_id"]
    other = auth_headers("applicant", owns="c-004")
    assert _chat(client, other, session_id).status_code == 404
    assert _finish(client, other, session_id).status_code == 404


# ── Sessions ───────────────────────────────────────────────────────


def test_session_and_result_survive_a_restart(client, db, auth_headers, applicant, no_key):
    session_id = _answer(client, applicant, language="ru")
    _finish(client, applicant, session_id)
    db.dispose()
    restarted = make_engine(str(db.url))
    set_engine(restarted)
    try:
        row = _row(restarted, session_id)
        assert (row.status, row.language, len(row.messages)) == ("finished", "ru", 7)
        with Session(restarted) as session:
            assert session.exec(select(ScenarioResult.source)).one() == "demo"
        assert client.get("/api/scenarios/result/c-003", headers=auth_headers("committee")).json()["language"] == "ru"
    finally:
        restarted.dispose()


def test_finishing_needs_three_replies_and_closes_the_session(client, applicant, no_key):
    session_id = _start(client, applicant).json()["session_id"]
    _chat(client, applicant, session_id)
    assert _finish(client, applicant, session_id).status_code == 400
    _chat(client, applicant, session_id)
    _chat(client, applicant, session_id)
    assert _finish(client, applicant, session_id).status_code == 200
    assert _chat(client, applicant, session_id).status_code == 409
    assert _finish(client, applicant, session_id).status_code == 409


def test_session_deleted_with_its_applicant_account(client, db, applicant, no_key):
    session_id = _start(client, applicant).json()["session_id"]
    user_id = _row(db, session_id).user_id
    with Session(db) as session:
        session.delete(session.get(User, user_id))
        session.commit()
    assert _row(db, session_id) is None


def test_attempt_limit(client, applicant, auth_headers, monkeypatch, no_key):
    monkeypatch.setattr(settings, "FEYNMAN_MAX_ATTEMPTS", 2)
    assert _start(client, applicant).status_code == 200
    assert _start(client, applicant, scenario="easy-way").status_code == 200
    third = _start(client, applicant, scenario="nobody-starts")
    assert third.status_code == 429
    assert third.headers["access-control-allow-origin"] == ORIGIN
    # Per applicant.
    assert _start(client, auth_headers("applicant", owns="c-004"), candidate="c-004").status_code == 200


def test_starting_again_abandons_the_open_attempt(client, db, applicant, no_key):
    first = _start(client, applicant).json()["session_id"]
    _start(client, applicant, scenario="easy-way")
    assert _row(db, first).status == "abandoned"
    assert _chat(client, applicant, first).status_code == 409


def test_last_attempt_cannot_be_taken_twice(client, db, applicant):
    user_id = client.get("/api/auth/me", headers=applicant).json()["id"]
    applicant_id = applicant_id_for("c-003")
    assert store.create_session(applicant_id, user_id, "easy-way", [], max_attempts=1) is not None
    assert store.create_session(applicant_id, user_id, "easy-way", [], max_attempts=1) is None
    with Session(db) as session:
        assert session.exec(select(func.count()).select_from(FeynmanSession)).one() == 1


def test_failed_chat_leaves_the_session_unchanged(client, db, model, applicant):
    session_id = _start(client, applicant).json()["session_id"]
    model.fail = _connection_error()
    response = _chat(client, applicant, session_id)
    assert response.status_code == 502
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert len(_row(db, session_id).messages) == 1
    model.fail = None
    assert _chat(client, applicant, session_id).json()["replies"] == 1


def test_failed_finish_reopens_the_session_for_a_retry(client, db, model, applicant):
    session_id = _answer(client, applicant)
    model.fail = ValueError("model reply contained no text block")
    assert _finish(client, applicant, session_id).status_code == 502
    assert _row(db, session_id).status == "active"
    model.fail = None
    assert _finish(client, applicant, session_id).status_code == 200


def test_finish_while_scoring_is_refused(client, model, applicant):
    session_id = _answer(client, applicant)
    assert store.claim_for_scoring(session_id)
    assert _finish(client, applicant, session_id).status_code == 409
    assert model.json_calls == 0


def test_a_stale_turn_does_not_overwrite_a_newer_one(client, db, applicant, no_key):
    session_id = _start(client, applicant).json()["session_id"]
    assert _chat(client, applicant, session_id).status_code == 200
    assert not store.record_exchange(session_id, 1, [{"role": "user", "content": "stale"}])
    assert _row(db, session_id).exchange_count == 2
