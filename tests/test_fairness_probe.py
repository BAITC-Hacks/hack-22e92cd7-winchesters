from __future__ import annotations

import pytest
from sqlmodel import Session, select

from backend.db.tables import AuditLogEntry

URL = "/api/fairness/probe/c-001"


@pytest.mark.parametrize("role", ["applicant", "interviewer"])
def test_probe_is_not_available_to_applicant_or_interviewer(client, auth_headers, role):
    assert client.post(URL, headers=auth_headers(role)).status_code == 403


@pytest.mark.parametrize("role", ["committee", "admin"])
def test_probe_returns_six_variants_without_changing_baseline_or_ranking(client, auth_headers, role):
    headers = auth_headers(role)
    before_score = client.post("/api/scoring/baseline/c-001", headers=headers).json()
    before_ranking = client.post("/api/scoring/rank?scorer=baseline", headers=headers).json()

    response = client.post(f"{URL}?live=false", headers=headers)
    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "cached_demo"
    assert len(body["variants"]) == 6
    assert body["changed_markers"] == ["name", "region", "school_type", "language", "speech_style", "name"]
    assert body["baseline"] == before_score

    after_score = client.post("/api/scoring/baseline/c-001", headers=headers).json()
    after_ranking = client.post("/api/scoring/rank?scorer=baseline", headers=headers).json()
    assert after_score == before_score
    assert after_ranking == before_ranking


def test_probe_audit_contains_prompt_and_model_identifiers(client, auth_headers, db):
    response = client.post(f"{URL}?live=false", headers=auth_headers("committee"))
    assert response.status_code == 200
    body = response.json()

    with Session(db) as session:
        entry = session.exec(
            select(AuditLogEntry)
            .where(AuditLogEntry.action == "fairness_probe_run")
            .order_by(AuditLogEntry.created_at.desc())
        ).first()

    assert entry is not None
    assert entry.object_id == "c-001"
    assert entry.after["prompt_id"] == body["prompt_id"]
    assert entry.after["model_id"] == body["model_id"]


def test_probe_falls_back_when_live_scorer_is_unavailable(client, auth_headers, monkeypatch):
    async def unavailable(*_args, **_kwargs):
        raise RuntimeError("model unavailable")

    monkeypatch.setattr("backend.routers.fairness.compute_ai_score", unavailable)
    response = client.post(URL, headers=auth_headers("committee"))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "fallback_demo"
    assert len(body["variants"]) == 6
    assert body["model_id"] == "cached-baseline-demo"
