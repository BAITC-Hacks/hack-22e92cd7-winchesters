from __future__ import annotations

import copy

from sqlmodel import Session, select

from backend.db.tables import CompetencyScore, ModelRun
from backend.evals.historical import build_funder_memo, build_report, compare_reports, replay_report


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


def test_fair13_replays_saved_ratings_byte_identically():
    report = build_report(_records())

    replayed = replay_report(report)
    comparison = compare_reports(report, replayed)

    assert comparison["byte_identical"] is True
    assert comparison["mismatches"] == []
    assert comparison["expected_hash"] == comparison["actual_hash"]
    assert report["reproducibility"]["rating_count"] == 40
    assert report["reproducibility"]["frozen_hashes"]["data"] == report["manifest"]["evaluation_data_hash"]


def test_fair14_funder_memo_projects_frozen_holdout_metrics():
    memo = build_funder_memo(build_report(_records()))

    assert memo["audience"] == "inDrive"
    assert memo["abstention"]["abstentions"] == 0
    assert memo["abstention"]["abstention_rate"] == 0.0
    assert {row["competency"] for row in memo["calibration"]} == {"leadership", "teamwork"}
    assert memo["provenance"]["holdout_sealed"] is True
    assert memo["provenance"]["report_hash"]
    assert memo["production_invariance"] == {"score_path_changed": False, "ranking_changed": False, "recommendation_changed": False}


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


def test_fair13_reproduction_is_staff_only_and_reports_mismatches(client, auth_headers, db):
    payload = {"records": _records()}
    assert client.post("/api/fairness/heldout/ingest", json=payload, headers=auth_headers("committee")).status_code == 200

    for role in ("applicant", "interviewer"):
        assert client.get("/api/fairness/heldout/reproduce", headers=auth_headers(role)).status_code == 403

    response = client.get("/api/fairness/heldout/reproduce", headers=auth_headers("admin"))
    assert response.status_code == 200
    assert response.json()["status"] == "reproduced"
    assert response.json()["ratings_recomputed"] == 40
    assert response.json()["provenance"]["cached_result"]["source"] == "saved_ratings"
    assert response.json()["provenance"]["fallback_result"] is None

    with Session(db) as session:
        run = session.exec(select(ModelRun).where(ModelRun.stage == "fair12_heldout")).first()
        output = copy.deepcopy(run.output)
        output["holdout"]["agreement"][0]["qwk"] = 0.25
        run.output = output
        session.add(run)
        session.commit()

    mismatch = client.get("/api/fairness/heldout/reproduce", headers=auth_headers("committee"))
    assert mismatch.status_code == 200
    body = mismatch.json()
    assert body["status"] == "mismatch"
    assert body["byte_identical"] is False
    assert any(item["path"] == "$.holdout.agreement[0].qwk" for item in body["mismatches"])


def test_fair14_funder_memo_is_staff_only_and_read_only(client, auth_headers, db):
    payload = {"records": _records()}
    for role in ("applicant", "interviewer"):
        assert client.get("/api/fairness/heldout/memo", headers=auth_headers(role)).status_code == 403

    assert client.post("/api/fairness/heldout/ingest", json=payload, headers=auth_headers("committee")).status_code == 200
    response = client.get("/api/fairness/heldout/memo", headers=auth_headers("admin"))
    assert response.status_code == 200
    body = response.json()
    assert body["audience"] == "inDrive"
    assert body["impact_ratios"] == body["holdout"]["impact_ratios"]
    assert body["production_invariance"]["score_path_changed"] is False
    assert len(list(Session(db).exec(select(CompetencyScore)))) == 0
