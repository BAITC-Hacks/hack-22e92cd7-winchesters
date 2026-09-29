"""Demo mode: ledgers without a model key, through the real quote check and level rules."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend import llm
from backend.db import ledger as ledger_store
from backend.ledger import demo, provenance
from backend.ledger.rubric import COMPETENCY_ORDER, RUBRIC
from backend.models import Candidate

SEED = Path(__file__).resolve().parents[1] / "backend" / "data" / "candidates.json"


def _seed_candidates() -> dict[str, Candidate]:
    return {raw["id"]: Candidate(**raw) for raw in json.loads(SEED.read_text(encoding="utf-8"))}


def test_every_authored_quote_is_the_applicants_own_words():
    candidates = _seed_candidates()
    authored = demo.load_authored()
    assert set(authored) == set(candidates)
    indicator_ids = {i.id for rubric in RUBRIC.values() for i in rubric.indicators}
    for ref, rows in authored.items():
        assert {row["indicator_id"] for row in rows} <= indicator_ids
        ledger = demo.build_demo_ledger(candidates[ref], rows)
        verified = [e for c in ledger.competencies for i in c.indicators for e in i.evidence]
        # A row whose quote is not in the documents is dropped, so equal counts
        # mean every authored quote matched character for character.
        assert len(verified) == len(rows), ref


def test_demo_ledgers_cover_all_nine_competencies_and_humans_keep_theirs():
    candidates = _seed_candidates()
    ledger = demo.build_demo_ledger(candidates["c-001"], demo.load_authored()["c-001"])
    assert [c.competency for c in ledger.competencies] == list(COMPETENCY_ORDER)
    for rating in ledger.competencies:
        if not RUBRIC[rating.competency].ai_may_rate:
            assert rating.reserved_for_humans and rating.level is None


def test_rule_based_ledger_quotes_only_verified_sentences_and_never_questions():
    candidate = _seed_candidates()["c-004"]
    ledger = demo.build_demo_ledger(candidate)
    assert ledger.model_judge == demo.DEMO_RULES
    quotes = [e for c in ledger.competencies for i in c.indicators for e in i.evidence]
    assert quotes and all(e.verified for e in quotes)
    assert not any(e.quote.rstrip().endswith("?") for e in quotes)


def test_demo_provenance_is_its_own_kind():
    ledger = demo.build_demo_ledger(_seed_candidates()["c-016"])
    described = provenance.describe(ledger)
    assert described["kind"] == "demo_mode" and described["illustrative"] is False


APPLICATION = {
    "name": "Dana Serik",
    "age": 17,
    "application": {"education": {"school_type": "public", "gpa": 3.6}, "languages": ["Kazakh", "English"]},
    "essay": {
        "prompt": "leadership",
        "text": (
            "Last spring our village school lost its only computer teacher. I started a coding club for "
            "twelve younger students and taught them every Saturday. Now three of them build games on their own."
        ),
    },
    "written_presentation": " ".join(["I organized volunteers to repair the library and now it opens every day."] * 12),
}


@pytest.mark.parametrize("key, expect_ledger", [("", True), ("sk-ant-real-looking-key", False)])
def test_a_new_application_gets_a_demo_ledger_only_without_a_key(client, auth_headers, monkeypatch, key, expect_ledger):
    monkeypatch.setattr(llm.client, "api_key", key)
    response = client.post("/api/candidates/", json=APPLICATION, headers=auth_headers("applicant"))
    assert response.status_code == 201, response.text
    ref = response.json()["id"]
    assert ledger_store.has_ledger(ref) is expect_ledger
    if expect_ledger:
        assert ledger_store.load_ledger(ref).model_judge == demo.DEMO_RULES
