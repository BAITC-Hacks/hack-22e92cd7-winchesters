"""LED-13: rubric and prompt versions carry the hash of their content, not of their label."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest
from sqlmodel import Session, select

from backend.committee_memo import build_decision_memo
from backend.committee_probe_bank import PROBE_BANK, PROBE_BANK_PROVENANCE
from backend.db import ledger as ledger_store
from backend.db.tables import PromptVersion, RubricVersion
from backend.ledger import pipeline, rubric, versions
from backend.ledger.schema import CandidateLedger, Competency

FIXTURE = Path(__file__).resolve().parents[1] / "backend" / "ledger" / "fixtures" / "ledger_example.json"


def _ledger() -> CandidateLedger:
    """The worked example, stamped as built under the current rubric."""
    ledger = CandidateLedger.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))
    ledger.rubric_version = rubric.RUBRIC_VERSION
    return ledger


def test_current_rubric_and_prompts_match_the_lock():
    """Fails when a rubric anchor or a prompt changes without a version bump.

    Fix: bump RUBRIC_VERSION or PROMPT_VERSION, then `python -m backend.ledger.versions --lock`.
    """
    for kind, (version, digest) in versions.current().items():
        assert versions.known_hash(kind, version) == digest, f"{kind} {version} changed without a version bump"


def test_rubric_hash_covers_anchor_wording(monkeypatch):
    before = versions.rubric_content_hash()
    leadership = rubric.RUBRIC[Competency.LEADERSHIP_ABILITIES]
    first = leadership.indicators[0]
    edited = dataclasses.replace(leadership, indicators=(dataclasses.replace(first, high=first.high + "!"),) + leadership.indicators[1:])
    monkeypatch.setitem(rubric.RUBRIC, Competency.LEADERSHIP_ABILITIES, edited)
    assert versions.rubric_content_hash() != before


def test_prompt_hash_covers_system_prompts(monkeypatch):
    before = versions.prompt_content_hash()
    monkeypatch.setattr(versions.rate, "RATING_SYSTEM", versions.rate.RATING_SYSTEM + " ")
    assert versions.prompt_content_hash() != before


def test_lock_refuses_to_rewrite_a_released_version(tmp_path, monkeypatch):
    lock_file = tmp_path / "versions.lock.json"
    versions.lock(lock_file)
    monkeypatch.setattr(versions, "rubric_content_hash", lambda: "0" * 64)
    with pytest.raises(ValueError, match="bump the version"):
        versions.lock(lock_file)


def test_saved_ledger_rows_carry_the_locked_content_hash(db):
    ledger_store.save_ledger("c-002", _ledger())
    with Session(db) as session:
        rubric_row = session.exec(select(RubricVersion).where(RubricVersion.version == rubric.RUBRIC_VERSION)).one()
        prompt_row = session.exec(select(PromptVersion).where(PromptVersion.version == pipeline.PROMPT_VERSION)).one()
    assert rubric_row.content_hash == versions.rubric_content_hash()
    assert prompt_row.content_hash == versions.prompt_content_hash()


def test_rows_written_with_a_label_hash_are_upgraded(db):
    import hashlib

    with Session(db) as session:
        session.add(RubricVersion(version=rubric.RUBRIC_VERSION, content_hash=hashlib.sha256(rubric.RUBRIC_VERSION.encode()).hexdigest()))
        session.commit()
    ledger_store.save_ledger("c-002", _ledger())
    with Session(db) as session:
        row = session.exec(select(RubricVersion).where(RubricVersion.version == rubric.RUBRIC_VERSION)).one()
    assert row.content_hash == versions.rubric_content_hash()


def test_a_released_version_with_different_content_is_refused(db):
    with Session(db) as session:
        session.add(RubricVersion(version=rubric.RUBRIC_VERSION, content_hash="f" * 64))
        session.commit()
    with pytest.raises(ValueError, match="bump the version"):
        ledger_store.save_ledger("c-002", _ledger())


def test_memo_shows_content_hashes_and_flags_unregistered_versions(db):
    ledger_store.save_ledger("c-002", _ledger())
    memo = build_decision_memo("c-002", ledger_store.load_ledger("c-002"))
    assert memo["provenance"]["rubric_hash"] == versions.rubric_content_hash()
    assert memo["provenance"]["prompt_hash"] == versions.prompt_content_hash()

    example = _ledger()
    example.prompt_version = "led-03-worked-example"
    ledger_store.save_ledger("c-003", example)
    memo = build_decision_memo("c-003", ledger_store.load_ledger("c-003"))
    assert memo["provenance"]["prompt_hash"].startswith("unregistered")


def test_rubric_endpoint_reports_draft_scales(client, auth_headers):
    assert client.get("/api/ledger/rubric", headers=auth_headers("interviewer")).status_code == 403
    body = client.get("/api/ledger/rubric", headers=auth_headers("committee")).json()
    assert body["version"] == rubric.RUBRIC_VERSION and body["locked"] is True
    assert len(body["competencies"]) == 9
    drafts = {item["competency"] for item in body["competencies"] if item["provisional"]}
    assert Competency.LEADERSHIP_ABILITIES.value not in drafts and len(drafts) == 7
    leadership = next(item for item in body["competencies"] if item["competency"] == "leadership_abilities")
    assert {"id": "lead.initiative", "label": "Initiative"} in leadership["indicators"]


def test_probe_bank_is_not_claimed_as_approved_before_the_methodology_arrives():
    assert PROBE_BANK_PROVENANCE["version"].startswith("com-06-provisional")
    assert all(item["approval_status"] == "provisional_pending_extended_methodology" for item in PROBE_BANK)
    assert all(item["leak_guard"]["checks"] == [] for item in PROBE_BANK)
