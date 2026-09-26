from __future__ import annotations

import json
import pathlib

from backend.committee_memo import build_decision_memo, render_pdf
from backend.ledger.schema import CandidateLedger


FIXTURE = pathlib.Path(__file__).resolve().parents[1] / "frontend" / "src" / "lib" / "fixtures" / "ledger_example.json"


def test_decision_memo_contains_evidence_bands_hashes_and_signature_lines(db):
    ledger = CandidateLedger.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))
    memo = build_decision_memo("a-7f3c2e91", ledger)
    assert memo["verified_quotes"]
    assert memo["competencies"][0]["bars_anchors"]["high"]
    assert {band["level"] for band in memo["test_bands"]} == {"weak", "normal", "high"}
    assert memo["provenance"]["model_hash"]
    assert memo["probe_result"]["status"] == "not_run"
    assert len(memo["signatures"]) == 2


def test_decision_memo_pdf_is_downloadable(db):
    ledger = CandidateLedger.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))
    pdf = render_pdf(build_decision_memo("a-7f3c2e91", ledger))
    assert pdf.startswith(b"%PDF-1.4")
    assert b"%%EOF" in pdf


def test_decision_memo_is_staff_only_and_has_pdf_route(client, auth_headers, monkeypatch):
    ledger = CandidateLedger.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))

    async def fake_build(_candidate):
        return ledger

    monkeypatch.setattr("backend.routers.committee.build_ledger", fake_build)
    for role in ("applicant", "interviewer"):
        assert client.get("/api/committee/decision-memo/c-001", headers=auth_headers(role, owns="c-001") if role == "applicant" else auth_headers(role)).status_code == 403
    headers = auth_headers("committee")
    override = client.post(
        "/api/overrides/c-001",
        headers=headers,
        json={"competency": "teamwork", "to_level": "high", "reason_code": "interview_evidence", "ai_level": "normal"},
    )
    assert override.status_code == 201
    response = client.get("/api/committee/decision-memo/c-001", headers=headers)
    assert response.status_code == 200
    assert response.json()["candidate_id"] == "c-001"
    assert response.json()["overrides"][0]["reason_code"] == "interview_evidence"
    assert response.json()["overrides"][0]["author"]["role"] == "committee"
    pdf = client.get("/api/committee/decision-memo/c-001/pdf", headers=headers)
    assert pdf.status_code == 200
    assert pdf.headers["content-type"].startswith("application/pdf")