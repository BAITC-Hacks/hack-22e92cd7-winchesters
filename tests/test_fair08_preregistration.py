from __future__ import annotations

from pathlib import Path

import pytest


DOCUMENT = Path(__file__).resolve().parents[1] / "docs" / "FAIR-08_PREREGISTRATION.md"
FAIRNESS_ENDPOINTS = ("/api/fairness/evaluation", "/api/fairness/audit")


def test_fair08_preregistration_locks_methodology_contracts():
    text = DOCUMENT.read_text(encoding="utf-8")
    required = (
        "2026-09-25",
        "Synthetic",
        "Cached",
        "Live",
        "Historical",
        "level-flip rate",
        "Repeat consistency",
        "Injection suite",
        "Cross-lingual agreement",
        "Noise tolerance",
        "2 x SD",
        "0.80",
        "n >= 10",
        "70% train / 30% holdout",
        "No prompt editing, rubric editing, seed selection, model selection, threshold selection",
        "prompt_id",
        "model_id",
        "rubric_id",
        "fixture_or_data_hash",
        "timestamp_utc",
        "FAIR-05",
        "FAIR-09",
        "production candidate scores, recommendations, ranking",
        "fairness-by-recommendation-category",
    )
    assert all(item in text for item in required)


@pytest.mark.parametrize("endpoint", FAIRNESS_ENDPOINTS)
def test_fair08_fairness_reports_are_staff_only(client, auth_headers, endpoint):
    for role in ("applicant", "interviewer"):
        assert client.get(endpoint, headers=auth_headers(role)).status_code == 403
    for role in ("committee", "admin"):
        assert client.get(endpoint, headers=auth_headers(role)).status_code == 200
