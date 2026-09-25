from __future__ import annotations

from sqlmodel import Session, select

from backend.db.tables import CompetencyScore
from backend.evals.historical import build_report


def _records(count: int = 20) -> list[dict]:
    return [
        {
            "applicant_id": f"history-{index}",
            "admitted": False,
            "attributes": {"region": "north" if index % 2 else "south", "application_language": "kk"},
            "ratings": [
                {
                    "competency": "teamwork",
                    "model_level": "high" if index % 3 else "normal",
                    "committee_level": "high" if index % 3 else "normal",
                    "human_levels": ["high", "high"],
                }
            ],
        }
        for index in range(count)
    ]


def test_fair09_report_is_applicant_split_and_has_registered_metrics():
    report = build_report(_records())

    assert report["split"] == {
        "train_applicants": 14,
        "holdout_applicants": 6,
        "train_rows": 14,
        "holdout_rows": 6,
        "holdout_sealed": True,
        "tuning_source": "train_only",
    }
    assert report["manifest"]["registration_id"] == "FAIR-08-2026-09-25"
    assert report["manifest"]["report_mode"] == "historical"
    agreement = report["train"]["agreement"][0]
    assert agreement["qwk"] == 1.0
    assert agreement["icc"] == 1.0
    assert agreement["human_human_qwk"] == 1.0
    assert agreement["calibration"]["high"]["high"] > 0
    assert report["holdout"]["screening_safety"]["safe"]


def test_fair09_missing_labels_are_reported_not_scored():
    records = _records()
    records[0]["ratings"][0]["model_level"] = None
    records[1]["ratings"][0]["committee_level"] = None

    report = build_report(records)

    assert report["failed_model_runs"] == 1
    assert report["missing_labels"] == 1
    assert report["train"]["agreement"][0]["n"] + report["holdout"]["agreement"][0]["n"] == 18


def test_fair09_ingest_is_staff_only_and_does_not_write_production_scores(client, auth_headers, db):
    before = len(list(Session(db).exec(select(CompetencyScore))))
    payload = {"records": _records()}
    for role in ("applicant", "interviewer"):
        assert client.post("/api/fairness/historical/ingest", json=payload, headers=auth_headers(role)).status_code == 403

    response = client.post("/api/fairness/historical/ingest", json=payload, headers=auth_headers("committee"))
    assert response.status_code == 200
    assert client.get("/api/fairness/historical/report", headers=auth_headers("admin")).status_code == 200
    after = len(list(Session(db).exec(select(CompetencyScore))))
    assert before == after