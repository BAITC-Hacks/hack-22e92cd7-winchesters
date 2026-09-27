from __future__ import annotations

from sqlmodel import Session, select

from backend.db.tables import AuditLogEntry, ModelRun
from backend.evals.harness import MARKERS, cached_report, gold_cases

URL = "/api/fairness/evaluation"


def test_gold_fixture_has_the_declared_36_case_shape():
    cases = gold_cases()
    assert len(cases) == 36
    assert {case.competency for case in cases} == {"leadership_abilities", "wounded_leadership"}
    assert {case.target_level for case in cases} == {"weak", "normal", "high"}
    assert {case.language for case in cases} == {"kk", "ru", "en"}
    assert {case.variant for case in cases} == {"concrete", "adversarial"}


def test_cached_report_is_reproducible_and_uses_all_fairness_metrics():
    first = cached_report()
    second = cached_report()
    assert first == second
    assert first["probe_count"] == 36 * len(MARKERS)
    assert first["repeat_count_per_case"] == 5
    assert first["injection_suite"]["passed"] is True
    assert first["tolerance"] == 0.0
    assert first["production_invariance"] == {
        "score_path_changed": False,
        "ranking_changed": False,
        "recommendation_changed": False,
    }


def test_evaluation_is_committee_admin_only(client, auth_headers):
    for role in ("applicant", "interviewer"):
        assert client.get(URL, headers=auth_headers(role)).status_code == 403
    for role in ("committee", "admin"):
        response = client.get(URL, headers=auth_headers(role))
        assert response.status_code == 200
        assert response.json()["status"] == "cached_demo"


def test_evaluation_records_reproducible_provenance_without_score_run(client, auth_headers, db):
    before = client.post("/api/scoring/rank?scorer=baseline", headers=auth_headers("committee")).json()
    response = client.get(URL, headers=auth_headers("committee"))
    assert response.status_code == 200
    report = response.json()
    after = client.post("/api/scoring/rank?scorer=baseline", headers=auth_headers("committee")).json()
    assert after == before

    with Session(db) as session:
        audit = session.exec(select(AuditLogEntry).where(AuditLogEntry.action == "fairness_evaluation_run")).first()
        runs = list(session.exec(select(ModelRun).where(ModelRun.stage == "eval_harness")))
    assert audit is not None
    assert audit.after["fixture_hash"] == report["fixture_hash"]
    assert audit.after["prompt_id"] == report["prompt_id"]
    assert runs and runs[-1].output["fixture_hash"] == report["fixture_hash"]


def test_live_failure_returns_cached_fallback(client, auth_headers, monkeypatch):
    async def unavailable():
        raise RuntimeError("no API key")

    monkeypatch.setattr("backend.routers.evaluation.live_report", unavailable)
    response = client.get(f"{URL}?live=true", headers=auth_headers("committee"))
    assert response.status_code == 200
    assert response.json()["status"] == "fallback_demo"
    assert response.json()["model_id"] == "cached-baseline-demo"


def test_cohort_probe_reports_marker_by_competency_and_cached_mode(client, auth_headers):
    response = client.get("/api/fairness/cohort-probe?live=false", headers=auth_headers("committee"))
    assert response.status_code == 200
    report = response.json()
    assert report["status"] == report["mode"] == "cached"
    assert 30 <= report["sampled_candidates"] <= 50
    assert report["live"] is None
    assert report["cached"]["mode"] == "cached"
    assert {cell["marker"] for cell in report["cells"]} == set(report["markers"])
    assert all(cell["sampled_candidates"] == report["sampled_candidates"] for cell in report["cells"])
    assert report["production_invariance"] == {
        "score_path_changed": False,
        "ranking_changed": False,
        "recommendation_changed": False,
    }


def test_cohort_probe_is_staff_only(client, auth_headers):
    for role in ("applicant", "interviewer"):
        assert client.get("/api/fairness/cohort-probe", headers=auth_headers(role)).status_code == 403


def test_publish_gate_blocks_a_failed_probe_without_audit_entry(client, auth_headers, monkeypatch, db):
    failed = {
        "status": "live",
        "mode": "live",
        "passed": False,
        "failed_cells": [{"marker": "region", "competency": "teamwork"}],
    }

    async def fail_probe(*_args, **_kwargs):
        return failed

    monkeypatch.setattr("backend.routers.fairness.cohort_probe.run", fail_probe)
    response = client.post("/api/fairness/scorer-versions/v1/publish", headers=auth_headers("committee"))
    assert response.status_code == 409
    with Session(db) as session:
        assert session.exec(select(AuditLogEntry).where(AuditLogEntry.action == "scorer_version_published")).first() is None
