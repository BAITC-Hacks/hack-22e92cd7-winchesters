"""FND-04, PR 3: model outputs live in `model_runs`, not in router caches.

What these pin: an AI score is stored and survives a restart; a failed run is
stored as failed (error, no output) and never ranks as a zero; `/all` routes
are reachable; the override endpoint no longer rewrites anything; a stored
video analysis is reused, while mock and failed ones are not served as
results. Everything runs offline: the scorers are replaced with fakes.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlmodel import Session, select

from backend.db import model_runs
from backend.db.candidates import applicant_id_for
from backend.db.engine import make_engine, set_engine
from backend.db.tables import ModelRun, PromptVersion
from backend.models import CandidateScore, DimensionScore, VideoAnalysisResult
from backend.routers import analysis, scoring

DIMENSIONS = ("academic_strength", "leadership_potential", "motivation_values", "growth_trajectory", "communication")


def _restart(db) -> None:
    """Drop every pooled connection and open the same file fresh."""
    url = db.url.render_as_string(hide_password=False)
    db.dispose()
    set_engine(make_engine(url))


def _score(candidate_id: str, value: float = 80.0) -> CandidateScore:
    return CandidateScore(
        candidate_id=candidate_id,
        dimensions=[DimensionScore(dimension=d, score=value, explanation=f"{d} looks fine") for d in DIMENSIONS],
        overall_score=value,
        recommendation="recommend",
        summary="Stored by a fake scorer.",
        scorer_type="ai",
    )


def _runs(db, stage: str) -> list[ModelRun]:
    with Session(db) as session:
        return list(session.exec(select(ModelRun).where(ModelRun.stage == stage)))


@pytest.fixture
def committee(auth_headers):
    return auth_headers("committee")


@pytest.fixture
def scorer(monkeypatch):
    """Fake AI scorer. Candidates listed in `failing` raise instead."""

    class Fake:
        failing: set[str] = set()
        calls = 0

        async def __call__(self, candidate, weights=None):
            self.calls += 1
            if candidate.id in self.failing:
                raise RuntimeError(f"upstream timeout for {candidate.id}")
            return _score(candidate.id)

    fake = Fake()
    monkeypatch.setattr(scoring, "compute_ai_score", fake)
    return fake


# ── Caches are gone ────────────────────────────────────────────────


def test_router_caches_are_gone():
    assert not hasattr(scoring, "_score_cache")
    assert not hasattr(scoring, "_baseline_cache")
    assert not hasattr(analysis, "_detection_cache")
    assert not hasattr(analysis, "_video_cache")


# ── record_model_run ───────────────────────────────────────────────


def test_versions_resolve_to_ids_and_unknown_ones_stay_null(db):
    with Session(db) as session:
        session.add(PromptVersion(version="led-04.0", content_hash="a" * 64))
        session.commit()
        prompt_id = session.exec(select(PromptVersion.id)).one()

    run_id = model_runs.record_model_run(
        stage="extract",
        model="claude-sonnet-5",
        status="ok",
        output={"items": []},
        prompt_version="led-04.0",
        rubric_version="never-registered",
    )

    with Session(db) as session:
        run = session.get(ModelRun, run_id)
        assert run.prompt_version_id == prompt_id
        assert run.rubric_version_id is None
        # The unknown version was not invented on the way.
        assert session.execute(text("SELECT count(*) FROM rubric_versions")).scalar_one() == 0


@pytest.mark.parametrize(
    "status,kwargs",
    [("ok", {}), ("failed", {}), ("failed", {"error": ""}), ("maybe", {"output": {}})],
)
def test_run_without_its_payload_is_rejected(db, status, kwargs):
    with pytest.raises(ValueError):
        model_runs.record_model_run(stage="score_ai", model="m", status=status, **kwargs)


def test_latest_ok_output_ignores_later_failures_and_older_oks(db):
    applicant = applicant_id_for("c-001")
    model_runs.record_model_run(stage="s", model="m", status="ok", output={"n": 1}, applicant_id=applicant)
    model_runs.record_model_run(stage="s", model="m", status="ok", output={"n": 2}, applicant_id=applicant)
    model_runs.record_model_run(stage="s", model="m", status="failed", error="boom", applicant_id=applicant)

    assert model_runs.latest_ok_output(applicant, "s") == {"n": 2}
    assert model_runs.latest_ok_output(applicant, "other-stage") is None
    assert model_runs.latest_ok_outputs("s") == {applicant: {"n": 2}}


# ── AI scores ──────────────────────────────────────────────────────


def test_ai_score_is_stored_and_survives_restart(client, db, committee, scorer):
    response = client.post("/api/scoring/ai/c-001", headers=committee)
    assert response.status_code == 200

    [run] = _runs(db, scoring.AI_SCORE_STAGE)
    assert run.status == "ok"
    assert run.applicant_id == applicant_id_for("c-001")
    assert CandidateScore.model_validate(run.output) == _score("c-001")

    _restart(db)
    compared = client.get("/api/scoring/compare/c-001", headers=committee)
    assert compared.status_code == 200
    assert compared.json()["ai_overall"] == 80.0

    ranked = client.post("/api/scoring/rank?scorer=ai", headers=committee).json()
    assert [r["candidate"]["id"] for r in ranked] == ["c-001"]
    assert ranked[0]["ai_score"]["summary"] == "Stored by a fake scorer."


def test_failed_scoring_is_stored_as_failed_and_not_ranked(client, db, committee, scorer):
    scorer.failing = {"c-002"}

    response = client.post("/api/scoring/ai/all", headers=committee)
    assert response.status_code == 200
    assert "c-002" not in {s["candidate_id"] for s in response.json()}
    assert len(response.json()) == 15

    failed = [r for r in _runs(db, scoring.AI_SCORE_STAGE) if r.status == "failed"]
    assert [r.applicant_id for r in failed] == [applicant_id_for("c-002")]
    assert "upstream timeout for c-002" in failed[0].error
    with Session(db) as session:
        # SQL NULL, not the JSON text 'null'.
        assert session.execute(
            text("SELECT count(*) FROM model_runs WHERE status = 'failed' AND output IS NULL")
        ).one()[0] == 1

    ranked = client.post("/api/scoring/rank?scorer=ai", headers=committee).json()
    assert len(ranked) == 15
    assert "c-002" not in {r["candidate"]["id"] for r in ranked}
    assert client.get("/api/scoring/compare/c-002", headers=committee).status_code == 404


def test_single_failed_scoring_is_500_and_recorded(client, db, committee, scorer):
    scorer.failing = {"c-003"}
    response = client.post("/api/scoring/ai/c-003", headers=committee)
    assert response.status_code == 500

    [run] = _runs(db, scoring.AI_SCORE_STAGE)
    assert (run.status, run.output) == ("failed", None)
    assert client.post("/api/scoring/rank?scorer=ai", headers=committee).json() == []


def test_baseline_rank_covers_everyone_and_is_not_stored(client, db, committee):
    ranked = client.post("/api/scoring/rank", headers=committee).json()
    assert len(ranked) == 16
    assert all(r["baseline_score"] for r in ranked)
    with Session(db) as session:
        assert session.execute(text("SELECT count(*) FROM model_runs")).scalar_one() == 0


# ── Route order (regression: "Candidate all not found") ────────────


@pytest.mark.parametrize("path", ["/api/scoring/baseline/all", "/api/scoring/ai/all"])
def test_all_routes_are_reachable(client, committee, scorer, path):
    response = client.post(path, headers=committee)
    assert response.status_code == 200, response.text
    assert len(response.json()) == 16


# ── Override ───────────────────────────────────────────────────────


def test_override_is_gone_and_changes_nothing(client, db, committee, scorer):
    client.post("/api/scoring/ai/c-001", headers=committee)
    response = client.post(
        "/api/scoring/override",
        headers=committee,
        json={"candidate_id": "c-001", "dimension": "communication", "override_score": 5, "note": "x"},
    )
    assert response.status_code == 410
    assert "COM-01" in response.json()["detail"]

    [run] = _runs(db, scoring.AI_SCORE_STAGE)
    assert CandidateScore.model_validate(run.output) == _score("c-001")


# ── Analysis ───────────────────────────────────────────────────────


@pytest.fixture
def video(monkeypatch):
    """Fake analyze_video; set `result` to what it returns."""

    class Fake:
        calls = 0
        result = VideoAnalysisResult(
            transcript="real words", language_detected="english", motivation_score=70, summary="Consistent."
        )

        async def __call__(self, candidate):
            self.calls += 1
            return self.result

    fake = Fake()
    monkeypatch.setattr(analysis, "analyze_video", fake)
    return fake


def test_video_analysis_is_stored_and_reused(client, db, committee, video):
    first = client.post("/api/analysis/video-analysis/c-001", headers=committee)
    assert first.status_code == 200

    _restart(db)
    second = client.post("/api/analysis/video-analysis/c-001", headers=committee)
    assert second.json() == first.json()
    assert video.calls == 1
    [run] = _runs(db, analysis.VIDEO_STAGE)
    assert run.status == "ok"


def test_mock_video_analysis_is_not_stored(client, db, committee, video):
    video.result = video.result.model_copy(update={"is_mock": True})
    assert client.post("/api/analysis/video-analysis/c-001", headers=committee).status_code == 200
    assert _runs(db, analysis.VIDEO_STAGE) == []


def test_swallowed_video_failure_is_stored_as_failed(client, db, committee, video):
    video.result = VideoAnalysisResult(
        transcript="real words",
        language_detected="kazakh",
        summary="Analysis unavailable — the transcript was not assessed.",
    )
    client.post("/api/analysis/video-analysis/c-001", headers=committee)
    client.post("/api/analysis/video-analysis/c-001", headers=committee)

    runs = _runs(db, analysis.VIDEO_STAGE)
    assert [(r.status, r.output) for r in runs] == [("failed", None), ("failed", None)]
    # Not served from storage: each request tries again.
    assert video.calls == 2


def test_ai_detection_is_computed_not_stored(client, db, committee):
    assert client.post("/api/analysis/ai-detection/c-001", headers=committee).status_code == 200
    results = client.get("/api/analysis/ai-detection/results", headers=committee)
    assert results.status_code == 200
    assert len(results.json()) == 16
    with Session(db) as session:
        assert session.execute(text("SELECT count(*) FROM model_runs")).scalar_one() == 0
