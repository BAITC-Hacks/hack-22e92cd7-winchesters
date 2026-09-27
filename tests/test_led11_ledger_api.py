"""LED-11 ledger API and LED-12 cached demo ledgers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.db import ledger as ledger_store
from backend.db.seed import seed_demo_ledger
from backend.ledger import atola, cache, pipeline
from backend.ledger.rubric import COMPETENCY_ORDER, RUBRIC
from backend.ledger.schema import CandidateLedger

FIXTURE = Path(__file__).resolve().parents[1] / "backend" / "ledger" / "fixtures" / "ledger_example.json"


def _ledger(ref: str = "c-001") -> CandidateLedger:
    ledger = CandidateLedger.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))
    ledger.applicant_ref = ref
    return ledger


def _variant(ref: str) -> CandidateLedger:
    """The worked example with one competency moved, so two candidates differ."""
    ledger = _ledger(ref)
    rating = next(r for r in ledger.competencies if not r.reserved_for_humans and r.level is not None)
    rating.contrastive = f"variant for {ref}"
    return ledger


def test_loaded_ledger_recomputes_derived_fields(db):
    ledger_store.save_ledger("c-002", _ledger("c-002"))
    loaded = ledger_store.load_ledger("c-002")
    expected = [atola.hydrate(r) for r in _ledger("c-002").competencies]
    assert any(r.atola_present for r in loaded.competencies)
    for want in expected:
        got = next(r for r in loaded.competencies if r.competency == want.competency)
        assert got.atola_present == want.atola_present
        assert sorted(i.capped_reason for i in got.indicators) == sorted(i.capped_reason for i in want.indicators)


def test_ledger_api_is_committee_and_admin_only(client, auth_headers):
    ledger_store.save_ledger("c-002", _ledger("c-002"))
    assert client.get("/api/ledger/c-002").status_code == 401
    assert client.get("/api/ledger/c-002", headers=auth_headers("applicant", owns="c-002")).status_code == 403
    assert client.get("/api/ledger/c-002", headers=auth_headers("interviewer")).status_code == 403
    assert client.get("/api/ledger", headers=auth_headers("interviewer")).status_code == 403
    for role in ("committee", "admin"):
        response = client.get("/api/ledger/c-002", headers=auth_headers(role))
        assert response.status_code == 200
        assert response.json()["applicant_ref"] == "c-002"


def test_ledger_api_reads_each_candidates_own_snapshot(client, auth_headers):
    ledger_store.save_ledger("c-002", _variant("c-002"))
    ledger_store.save_ledger("c-003", _variant("c-003"))
    headers = auth_headers("committee")
    two = client.get("/api/ledger/c-002", headers=headers).json()
    three = client.get("/api/ledger/c-003", headers=headers).json()
    assert "variant for c-002" in json.dumps(two) and "variant for c-003" in json.dumps(three)
    listed = client.get("/api/ledger", headers=headers).json()
    assert [item["applicant_ref"] for item in listed] == ["c-002", "c-003"]


def test_missing_ledger_is_404_and_never_a_live_rebuild(client, auth_headers, monkeypatch):
    async def forbidden(*_args, **_kwargs):
        raise AssertionError("the API must not call the model")

    monkeypatch.setattr(pipeline, "build_ledger", forbidden)
    headers = auth_headers("committee")
    missing = client.get("/api/ledger/c-004", headers=headers)
    assert missing.status_code == 404
    assert "ledger has been built" in missing.json()["detail"]
    assert client.get("/api/ledger/c-999", headers=headers).status_code == 404
    assert client.get("/api/ledger", headers=headers).json() == []


def test_seed_loads_cache_idempotently_and_labels_the_worked_example(db, tmp_path):
    cache.write_cached(_variant("c-005"), tmp_path)
    assert seed_demo_ledger(tmp_path) == 2
    assert seed_demo_ledger(tmp_path) == 0
    assert "variant for c-005" in json.dumps(ledger_store.load_ledger("c-005").model_dump(mode="json"))
    example = ledger_store.load_ledger("c-001")
    assert example.model_judge == example.model_extract == "hand-authored"
    assert example.prompt_version == "led-03-worked-example"

    rebuilt = _variant("c-005")
    rebuilt.competencies[0].contrastive = "rebuilt"
    cache.write_cached(rebuilt, tmp_path)
    assert seed_demo_ledger(tmp_path) == 1
    assert "rebuilt" in json.dumps(ledger_store.load_ledger("c-005").model_dump(mode="json"))


def test_cached_c001_replaces_the_worked_example(db, tmp_path):
    cache.write_cached(_variant("c-001"), tmp_path)
    seed_demo_ledger(tmp_path)
    assert ledger_store.load_ledger("c-001").prompt_version == _ledger().prompt_version


def _empty_ledger(ref: str) -> CandidateLedger:
    ledger = CandidateLedger(applicant_ref=ref, rubric_version="r", model_judge="m", model_extract="m", prompt_version="p")
    ledger.competencies = [pipeline.empty_rating(RUBRIC[c]) for c in COMPETENCY_ORDER]
    return ledger


def test_an_all_empty_run_is_treated_as_failed():
    assert cache.looks_failed(_empty_ledger("c-001"))
    assert not cache.looks_failed(_ledger())


@pytest.mark.asyncio
async def test_build_writes_skips_and_refuses_to_cache_failures(db, tmp_path, monkeypatch):
    async def fake_build(candidate):
        return _empty_ledger(candidate.id) if candidate.id == "c-003" else _variant(candidate.id)

    monkeypatch.setattr(pipeline, "build_ledger", fake_build)
    outcomes = await cache.build(["c-002", "c-003", "c-999"], cache_dir=tmp_path)
    assert outcomes == {"c-002": "written", "c-003": "failed", "c-999": "missing"}
    assert cache.cached_refs(tmp_path) == ["c-002"]
    assert (await cache.build(["c-002"], cache_dir=tmp_path)) == {"c-002": "skipped"}
    assert (await cache.build(["c-002"], force=True, cache_dir=tmp_path)) == {"c-002": "written"}


def test_cli_refuses_to_run_without_an_api_key(monkeypatch, capsys):
    monkeypatch.setattr("dotenv.load_dotenv", lambda *_a, **_k: False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert cache.main([]) == 2
    assert "ANTHROPIC_API_KEY" in capsys.readouterr().err
