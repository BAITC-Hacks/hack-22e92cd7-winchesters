"""INP-01: the written presentation is the canonical input; a mock is never scored.

What these pin:
- the written presentation is its own field, 150–300 words inclusive, in any
  language, counted by whitespace so Kazakh and code-switched text count right;
- the ledger reads it from that field, and the video transcript is not a
  ledger source;
- video analysis without a transcript returns `no_transcript`, no numbers, and
  never calls a model; no API response carries the old mock text;
- ASR is ElevenLabs Scribe v2 behind a flag and a key, and says "unavailable"
  otherwise; Whisper is gone;
- length and language never reach a score.

Everything runs offline; any model call fails the test.
"""

from __future__ import annotations

import copy
import inspect
import json
import pathlib

import pytest

from backend import llm, settings
from backend.db import candidates as store
from backend.db.tables import ArtifactKind
from backend.ledger import pipeline
from backend.ledger.schema import Source
from backend.models import (
    WRITTEN_PRESENTATION_MAX_WORDS,
    WRITTEN_PRESENTATION_MIN_WORDS,
    Candidate,
    count_words,
)
from backend.scoring import video_analyzer
from backend.scoring.baseline import compute_baseline_score
from tests.test_db_core import _new_application

DATA = pathlib.Path(__file__).resolve().parents[1] / "backend" / "data" / "candidates.json"

# Test text, not seed data. Kazakh-specific letters (ә ғ қ ң ө ұ ү і) on purpose.
KAZAKH = "Мен ауылдағы балаларға математикадан тегін сабақ бердім және олардың қиындықтарын түсіндім".split()
MIXED = "Біз volunteers тобын құрдық, потом мы вместе собрали деньги для школьной библиотеки".split()

# Phrases from the retired MOCK_TRANSCRIPT; none may ever reach a response.
MOCK_PHRASES = (
    "organize transport for families who couldn't get to the city",
    "defend my numbers",
    "MOCK_TRANSCRIPT",
    "is_mock",
)


def _words(n: int, vocabulary: list[str] = KAZAKH) -> str:
    return " ".join(vocabulary[i % len(vocabulary)] for i in range(n))


def _application(written: str) -> dict:
    body = _new_application()
    body["written_presentation"] = written
    return body


@pytest.fixture
def no_model(monkeypatch):
    """Fail the test on any attempt to call a model."""

    async def refuse(*args, **kwargs):
        raise AssertionError("a model was called")

    monkeypatch.setattr(llm, "complete_json", refuse)
    monkeypatch.setattr(llm, "complete_text", refuse, raising=False)


# ── Word counting ──────────────────────────────────────────────────


def test_kazakh_words_are_counted_by_whitespace():
    text = "Ешкім бастамаған соң, мен өзім бастадым Қазақстанның ауылдарында."
    assert count_words(text) == 8


def test_mixed_language_newlines_and_nbsp_count_as_separators():
    text = "Мен\nvolunteer болдым,\tпотом мы   собрали деньги"
    assert count_words(text) == 7


# ── Validation on submission ───────────────────────────────────────


@pytest.mark.parametrize(
    "words, accepted",
    [
        (WRITTEN_PRESENTATION_MIN_WORDS - 1, False),
        (WRITTEN_PRESENTATION_MIN_WORDS, True),
        (WRITTEN_PRESENTATION_MAX_WORDS, True),
        (WRITTEN_PRESENTATION_MAX_WORDS + 1, False),
    ],
)
def test_bounds_are_inclusive(client, auth_headers, words, accepted):
    response = client.post("/api/candidates/", json=_application(_words(words)), headers=auth_headers("applicant"))
    assert response.status_code == (201 if accepted else 422), response.text


def test_the_error_says_what_is_wrong(client, auth_headers):
    response = client.post("/api/candidates/", json=_application(_words(149)), headers=auth_headers("applicant"))
    message = json.dumps(response.json(), ensure_ascii=False)
    assert "150–300 words" in message
    assert "it has 149" in message


def test_an_application_without_a_written_presentation_is_accepted(client, auth_headers):
    body = _new_application()
    del body["written_presentation"]
    response = client.post("/api/candidates/", json=body, headers=auth_headers("applicant"))
    assert response.status_code == 201, response.text
    assert response.json()["written_presentation"] == ""


def test_kazakh_text_of_150_words_is_accepted_and_stored(client, auth_headers):
    text = _words(150)
    response = client.post("/api/candidates/", json=_application(text), headers=auth_headers("applicant"))
    assert response.status_code == 201
    created = response.json()
    assert created["written_presentation"] == text
    assert store.get_candidate(created["id"]).written_presentation == text


def test_code_switched_text_is_accepted(client, auth_headers):
    response = client.post("/api/candidates/", json=_application(_words(200, MIXED)), headers=auth_headers("applicant"))
    assert response.status_code == 201


def test_it_is_stored_as_its_own_artifact_kind(db):
    created = store.create_candidate(Candidate(id="", **_application(_words(150))))
    from sqlmodel import Session, select

    from backend.db.tables import Artifact

    with Session(db) as session:
        applicant_id = store.applicant_id_for(created.id)
        kinds = set(session.exec(select(Artifact.kind).where(Artifact.applicant_id == applicant_id)))
    assert ArtifactKind.WRITTEN_PRESENTATION.value in kinds
    assert ArtifactKind.VIDEO_TRANSCRIPT.value not in kinds


# ── Authorization on the changed endpoints ─────────────────────────


@pytest.mark.parametrize("role", ["committee", "interviewer", "admin"])
def test_only_applicants_submit(client, auth_headers, role):
    response = client.post("/api/candidates/", json=_application(_words(150)), headers=auth_headers(role))
    assert response.status_code == 403


def test_submission_needs_a_login(client):
    assert client.post("/api/candidates/", json=_application(_words(150))).status_code == 401


@pytest.mark.parametrize("role, allowed", [("committee", True), ("admin", True), ("applicant", False), ("interviewer", False)])
def test_video_analysis_is_staff_only(client, auth_headers, no_model, role, allowed):
    headers = auth_headers(role)
    assert client.post("/api/analysis/video-analysis/c-001", headers=headers).status_code == (200 if allowed else 403)
    assert client.get("/api/analysis/video-analysis/status", headers=headers).status_code == (200 if allowed else 403)


def test_video_analysis_needs_a_login(client):
    assert client.post("/api/analysis/video-analysis/c-001").status_code == 401
    assert client.get("/api/analysis/video-analysis/status").status_code == 401


# ── The ledger reads the new field ─────────────────────────────────


def _seed(index: int = 0) -> Candidate:
    return Candidate(**json.loads(DATA.read_text(encoding="utf-8"))[index])


def test_ledger_reads_the_written_presentation_field():
    candidate = _seed()
    candidate.written_presentation = _words(150)
    candidate.video_transcript = "spoken words that are not the written presentation"

    sources = pipeline.collect_sources(candidate)
    assert sources[Source.WRITTEN_PRESENTATION] == candidate.written_presentation
    assert Source.VIDEO_TRANSCRIPT not in sources
    assert candidate.video_transcript not in sources.values()


def test_a_video_transcript_alone_is_not_a_written_presentation():
    candidate = _seed()
    candidate.written_presentation = ""
    candidate.video_transcript = _words(200)
    assert Source.WRITTEN_PRESENTATION not in pipeline.collect_sources(candidate)


def test_seed_written_presentations_are_empty_or_in_bounds():
    """No seed applicant had a text that is a written presentation, so the field
    is empty for them rather than filled with something invented."""
    for raw in json.loads(DATA.read_text(encoding="utf-8")):
        text = Candidate(**raw).written_presentation
        assert not text or WRITTEN_PRESENTATION_MIN_WORDS <= count_words(text) <= WRITTEN_PRESENTATION_MAX_WORDS


# ── Never score a mock ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_no_transcript_means_no_numbers_and_no_model(no_model, monkeypatch):
    # Even with a key present, nothing is sent: there is nothing of theirs to read.
    monkeypatch.setattr(llm, "is_configured", lambda: True)
    candidate = _seed()
    candidate.video_transcript = "   "

    result = await video_analyzer.analyze_video(candidate)

    assert result.status == "no_transcript"
    assert result.authenticity_match is None
    assert result.motivation_score is None
    assert result.transcript == ""
    assert not result.key_themes and not result.growth_signals and not result.concerns


@pytest.mark.asyncio
async def test_a_transcript_without_a_model_key_is_unavailable_not_scored(no_model, monkeypatch):
    monkeypatch.setattr(llm, "is_configured", lambda: False)
    candidate = _seed()
    candidate.video_transcript = "Сәлеметсіз бе, мен өз жобам туралы айтамын."

    result = await video_analyzer.analyze_video(candidate)

    assert result.status == "unavailable"
    assert result.authenticity_match is None and result.motivation_score is None


def test_the_mock_transcript_is_gone():
    source = inspect.getsource(video_analyzer)
    assert "MOCK_TRANSCRIPT" not in source
    assert "whisper-1" not in source
    assert "openai" not in source.lower()


def test_no_api_response_carries_the_mock(client, auth_headers, no_model):
    headers = auth_headers("committee")
    bodies = [client.get("/api/candidates/", headers=headers).text]
    bodies.append(client.get("/api/analysis/video-analysis/status", headers=headers).text)
    for candidate in json.loads(DATA.read_text(encoding="utf-8")):
        response = client.post(f"/api/analysis/video-analysis/{candidate['id']}", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "no_transcript"
        assert body["authenticity_match"] is None and body["motivation_score"] is None
        bodies.append(response.text)

    for text in bodies:
        for phrase in MOCK_PHRASES:
            assert phrase not in text, phrase


def test_no_transcript_is_not_stored_as_a_model_run(client, auth_headers, db, no_model):
    from sqlmodel import Session, select

    from backend.db.tables import ModelRun

    client.post("/api/analysis/video-analysis/c-001", headers=auth_headers("committee"))
    with Session(db) as session:
        assert session.exec(select(ModelRun).where(ModelRun.stage == "video_analysis")).all() == []


# ── ASR: Scribe v2 behind a flag, never Whisper ────────────────────


def test_asr_is_pinned_to_scribe_v2():
    assert settings.ASR_PROVIDER == "elevenlabs"
    assert settings.ASR_MODEL == "scribe_v2"


def test_asr_is_unavailable_without_the_flag(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "ASR_ENABLED", False)
    monkeypatch.setattr(settings, "ELEVENLABS_API_KEY", "")
    body = client.get("/api/analysis/video-analysis/status", headers=auth_headers("committee")).json()
    assert body["asr"]["available"] is False
    assert body["asr"]["reason"].startswith("ASR unavailable")
    assert "whisper" not in json.dumps(body).lower()


def test_asr_needs_the_key_as_well_as_the_flag(monkeypatch):
    monkeypatch.setattr(settings, "ASR_ENABLED", True)
    monkeypatch.setattr(settings, "ELEVENLABS_API_KEY", "")
    status = video_analyzer.asr_status()
    assert status["available"] is False
    assert "ELEVENLABS_API_KEY" in status["reason"]

    monkeypatch.setattr(settings, "ELEVENLABS_API_KEY", "set")
    assert video_analyzer.asr_status()["available"] is True


# ── Length and language are not score inputs ───────────────────────


def test_written_presentation_length_and_language_do_not_move_the_score():
    base = _seed()
    scores = set()
    for text in ("", _words(150), _words(300), _words(300, MIXED), _words(150, "I helped my village school".split())):
        twin = copy.deepcopy(base)
        twin.written_presentation = text
        scores.add(compute_baseline_score(twin).overall_score)
    assert len(scores) == 1, scores
