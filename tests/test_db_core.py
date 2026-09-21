"""FND-04, PR 1: applicants, artifacts and users live in the database.

What these pin: the 16 demo records survive the move without loss, data
survives a restart, ids cannot collide, the API contract the frontend reads is
unchanged, and the app refuses to start on an unmigrated database.
"""

from __future__ import annotations

import json
import pathlib
import uuid

import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from backend.db import candidates as store
from backend.db.engine import SchemaNotCurrent, alembic_config, make_engine, set_engine
from backend.db.seed import DEMO_COMMITTEE_EMAIL, DEMO_COMMITTEE_PASSWORD, seed
from backend.db.tables import Applicant, Artifact
from backend.models import Candidate

SEED = pathlib.Path(__file__).resolve().parents[1] / "backend" / "data" / "candidates.json"


def _seed_records() -> list[Candidate]:
    return [Candidate(**raw) for raw in json.loads(SEED.read_text(encoding="utf-8"))]


def _new_application(name: str = "Test Applicant") -> dict:
    return {
        "name": name,
        "age": 17,
        "application": {
            "education": {"school_type": "public", "gpa": 3.5, "academic_achievements": []},
            "extracurriculars": [],
            "projects": [],
            "languages": ["kk", "ru"],
            "skills": [],
        },
        "essay": {"prompt": "Why inVision U?", "text": "I started a tutoring circle in my village."},
        "interview_transcript": "",
        "recommendation_summary": "",
    }


def _restart(db) -> None:
    """Drop every pooled connection and open the same file fresh: what a
    process restart looks like to the data."""
    url = db.url.render_as_string(hide_password=False)
    db.dispose()
    set_engine(make_engine(url))


# ── Seed ───────────────────────────────────────────────────────────


def test_seed_loads_all_16_and_is_idempotent(db):
    assert len(store.list_candidates()) == 16
    again = seed()
    assert again.applicants_added == 0
    assert not again.demo_user_added
    assert len(store.list_candidates()) == 16


def test_seed_round_trip_is_lossless_except_derived_word_count(db):
    """Every field the frontend and scorer read comes back as it went in.

    `essay.word_count` is recomputed from the text rather than stored; one
    record (c-014, Kazakh) was generated with a count that disagrees with
    `len(text.split())`, and consistency with every newly submitted essay wins.
    """
    stored = {c.id: c for c in store.list_candidates()}
    for original in _seed_records():
        got = stored[original.id].model_dump()
        want = original.model_dump()
        got["essay"].pop("word_count")
        want["essay"].pop("word_count")
        assert got == want, original.id


def test_list_keeps_seed_order(db):
    assert [c.id for c in store.list_candidates()] == [c.id for c in _seed_records()]


def test_applicant_key_is_a_uuid_and_the_old_id_is_a_legacy_ref(db):
    with Session(db) as session:
        applicant = session.exec(select(Applicant).where(Applicant.legacy_ref == "c-001")).one()
    assert uuid.UUID(applicant.id)
    # Either handle finds the same applicant: FND-07 can switch the API to
    # UUIDs without a data migration.
    assert store.get_candidate(applicant.id).id == "c-001"


def test_empty_texts_are_not_stored_as_artifacts(db):
    with Session(db) as session:
        kinds = session.exec(select(Artifact.kind)).all()
    # 16 essays, 15 interviews, 15 recommendations, no video in the seed.
    assert sorted(set(kinds)) == ["essay", "interview_transcript", "recommendation"]
    assert kinds.count("essay") == 16


# ── Candidates API ─────────────────────────────────────────────────


def test_list_candidates_endpoint(client):
    response = client.get("/api/candidates/")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 16
    assert body[0]["id"] == "c-001"


def test_unknown_candidate_is_404(client):
    assert client.get("/api/candidates/c-999").status_code == 404


def test_created_candidate_gets_next_id_and_survives_restart(client, db):
    response = client.post("/api/candidates/", json=_new_application())
    assert response.status_code == 201
    created = response.json()
    assert created["id"] == "c-017"
    assert created["essay"]["word_count"] == 8

    _restart(db)
    assert store.get_candidate("c-017").name == "Test Applicant"


def test_id_collision_is_retried_not_duplicated(db, monkeypatch):
    """Two submissions racing for the same `c-###` must not share it: the
    unique constraint rejects the loser and it takes the next number."""
    real = store._next_legacy_ref
    handed_out = iter(["c-016"])  # already taken by the seed

    def colliding_then_real(session):
        return next(handed_out, None) or real(session)

    monkeypatch.setattr(store, "_next_legacy_ref", colliding_then_real)
    created = store.create_candidate(Candidate(id="", **_new_application()))
    assert created.id == "c-017"
    assert len(store.list_candidates()) == 17


def test_foreign_keys_are_enforced(db):
    """SQLite ignores FKs unless each connection turns them on."""
    with Session(db) as session:
        session.add(Artifact(applicant_id=str(uuid.uuid4()), kind="essay", content="orphan"))
        with pytest.raises(IntegrityError):
            session.commit()


# ── Users ──────────────────────────────────────────────────────────


def test_register_login_me_and_survive_restart(client, db):
    registered = client.post(
        "/api/auth/register", json={"email": "a@example.kz", "password": "secret1", "full_name": "Aigerim"}
    )
    assert registered.status_code == 200
    assert uuid.UUID(registered.json()["user"]["id"])

    _restart(db)
    login = client.post("/api/auth/login", json={"email": "a@example.kz", "password": "secret1"})
    assert login.status_code == 200
    token = login.json()["token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["email"] == "a@example.kz"
    assert me.json()["role"] == "applicant"


def test_wrong_password_and_duplicate_email(client):
    payload = {"email": "b@example.kz", "password": "secret1", "full_name": "B"}
    assert client.post("/api/auth/register", json=payload).status_code == 200
    assert client.post("/api/auth/register", json=payload).status_code == 400
    wrong = client.post("/api/auth/login", json={"email": "b@example.kz", "password": "nope"})
    assert wrong.status_code == 401


def test_link_candidate_persists_and_rejects_unknown_ids(client):
    token = client.post(
        "/api/auth/register", json={"email": "c@example.kz", "password": "secret1", "full_name": "C"}
    ).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    assert client.post("/api/auth/link-candidate?candidate_id=c-999", headers=headers).status_code == 404
    assert client.post("/api/auth/link-candidate?candidate_id=c-005", headers=headers).status_code == 200
    assert client.get("/api/auth/me", headers=headers).json()["candidate_id"] == "c-005"


def test_demo_committee_account_is_seeded(client):
    login = client.post(
        "/api/auth/login", json={"email": DEMO_COMMITTEE_EMAIL, "password": DEMO_COMMITTEE_PASSWORD}
    )
    assert login.status_code == 200
    assert login.json()["user"]["role"] == "committee"


# ── Schema lifecycle ───────────────────────────────────────────────


def test_app_refuses_to_start_on_an_unmigrated_database(tmp_path):
    from backend.main import app

    set_engine(make_engine(f"sqlite:///{(tmp_path / 'empty.db').as_posix()}"))
    try:
        with pytest.raises(SchemaNotCurrent, match="python -m backend.db init"):
            with TestClient(app):
                pass
    finally:
        set_engine(None)


def test_migrations_downgrade_and_upgrade_cleanly(tmp_path):
    config = alembic_config(f"sqlite:///{(tmp_path / 'cycle.db').as_posix()}")
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    command.upgrade(config, "head")
