from __future__ import annotations

from sqlmodel import Session, select

from backend.db.tables import CompetencyScore, ModelRun
from backend.evals.historical import build_report


def _records(count: int = 20) -> list[dict]:
    return [
        {
            "applicant_id": f"fair12-{index}",
            "admitted": index == 0,
            "attributes": {"region": "north" if index % 2 else "south", "application_language": "kk"},
            "ratings": [
                {
                    "competency": "leadership",
                    "model_level": "weak" if index == 0 else "high",
                    "committee_level": "weak" if index == 0 else "high",
                    "human_levels": ["high", "high"],
                },
                {
                    "competency": "teamwork",
                    "model_level": "normal",
                    "committee_level": "normal",
                    "human_levels": ["normal", "normal"],
                },
            ],
        }
        for index in range(count)
    ]


def test_fair12_report_freezes_holdout_provenance_and_invariance():
    report = build_report(_records())

    assert report["manifest"]["report_mode"] == "historical"
    assert report["provenance"] == {
        "requested_mode": "historical",
        "effective_mode": "historical",
        "fallback_used": False,
        "fallback_reason": None,
        "live_result": None,
        "cached_result": None,
    }
    assert report["split"]["holdout_sealed"] is True
    assert report["split"]["tuning_source"] == "train_only"
    assert report["production_invariance"] == {
        "score_path_changed": False,
        "ranking_changed": False,
        "recommendation_changed": False,
    }
    assert {row["competency"] for row in report["holdout"]["agreement"]} == {"leadership", "teamwork"}
    assert all(row["qwk"] == 1.0 and row["icc"] == 1.0 for row in report["holdout"]["agreement"])
    assert report["holdout"]["screening_safety"]["admitted_in_lowest_band"] == 0
    assert report["holdout"]["screening_safety"]["safe"] is True


def test_fair12_endpoint_is_staff_only_and_does_not_write_scores(client, auth_headers, db):
    before_scores = len(list(Session(db).exec(select(CompetencyScore))))
    payload = {"records": _records()}

    for role in ("applicant", "interviewer"):
        assert client.post("/api/fairness/heldout/ingest", json=payload, headers=auth_headers(role)).status_code == 403
        assert client.get("/api/fairness/heldout/report", headers=auth_headers(role)).status_code == 403

    response = client.post("/api/fairness/heldout/ingest", json=payload, headers=auth_headers("committee"))
    assert response.status_code == 200
    body = response.json()
    assert body["holdout"]["screening_safety"]["safe"] is True
    assert client.get("/api/fairness/heldout/report", headers=auth_headers("admin")).status_code == 200
    assert len(list(Session(db).exec(select(CompetencyScore)))) == before_scores
    assert len(list(Session(db).exec(select(ModelRun).where(ModelRun.stage == "fair12_heldout")))) == 1
