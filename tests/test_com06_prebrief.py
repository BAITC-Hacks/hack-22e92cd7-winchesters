from __future__ import annotations

import json
from pathlib import Path

from backend.committee_prebrief import build_prebrief
from backend.db.ledger import save_ledger
from backend.ledger.schema import CandidateLedger


FIXTURE = Path(__file__).resolve().parents[1] / "frontend" / "src" / "lib" / "fixtures" / "ledger_example.json"


def _ledger() -> CandidateLedger:
    return CandidateLedger.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))


def test_prebrief_selects_competency_missing_component_and_withholds_score():
    brief = build_prebrief(_ledger())
    assert brief["score_withheld"] is True
    assert len(brief["strengths"]) == 2
    row = next(item for item in brief["rows"] if item["competency"] == "leadership_abilities")
    assert row["missing_components"]
    assert row["probe"]["probe_id"] == f"leadership_abilities.{row['missing_components'][0]}"
    assert row["probe"]["canonical"]
    assert row["probe"]["paraphrase"]
    assert all("level" not in item for item in brief["rows"])


def test_prebrief_endpoint_is_staff_only_and_reads_persisted_ledger(client, auth_headers):
    save_ledger("c-001", _ledger())
    assert client.get("/api/committee/pre-brief/c-001").status_code == 401
    assert client.get("/api/committee/pre-brief/c-001", headers=auth_headers("applicant", owns="c-001")).status_code == 403
    response = client.get("/api/committee/pre-brief/c-001", headers=auth_headers("committee"))
    assert response.status_code == 200
    assert response.json()["candidate_id"] == "c-001"
    assert response.json()["score_withheld"] is True
    assert "level" not in response.json()


def test_prebrief_does_not_live_rebuild_missing_ledger(client, auth_headers):
    response = client.get("/api/committee/pre-brief/c-001", headers=auth_headers("committee"))
    assert response.status_code == 409