from __future__ import annotations

import json
import pathlib

from backend.committee_memo import build_decision_memo, render_pdf
from backend.db.ledger import save_ledger
from backend.ledger.schema import CandidateLedger


FIXTURE = pathlib.Path(__file__).resolve().parents[1] / "backend" / "ledger" / "fixtures" / "ledger_example.json"


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
    assert pdf.startswith(b"%PDF-")
    assert b"%%EOF" in pdf
    assert b"/Subtype /TrueType" in pdf


def test_decision_memo_is_staff_only_and_has_pdf_route(client, auth_headers):
    ledger = CandidateLedger.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))
    save_ledger("c-001", ledger)
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


def test_decision_memo_supports_kazakh_and_append_only_signatures(client, auth_headers):
    ledger = CandidateLedger.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))
    save_ledger("c-001", ledger)
    headers = auth_headers("committee")
    memo = client.get("/api/committee/decision-memo/c-001?locale=kk", headers=headers)
    assert memo.status_code == 200
    assert memo.json()["locale"] == "kk"
    assert client.post("/api/committee/decision-memo/c-001/signatures/chair", headers=headers).status_code == 201
    assert client.post("/api/committee/decision-memo/c-001/signatures/chair", headers=headers).status_code == 409
    assert client.post("/api/committee/decision-memo/c-001/signatures/member", headers=headers).status_code == 201
    signed = client.get("/api/committee/decision-memo/c-001", headers=headers)
    assert {item["role"] for item in signed.json()["signatures"]} == {"chair", "member"}
    assert client.post("/api/committee/decision-memo/c-001/signatures/chair", headers=auth_headers("applicant", owns="c-001")).status_code == 403