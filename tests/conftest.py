"""Shared fixtures.

`db` gives each test its own SQLite file with the real migrations applied and
the seed loaded. Migrating once per session and copying the file per test keeps
that fast, and running the actual Alembic migrations here means CI fails on a
broken migration, not just on broken code.

`auth_headers` mints a bearer token for a fresh user of any role, so a test
states who is calling without going through registration.
"""

from __future__ import annotations

import os
import shutil
import uuid

# Before any backend import: settings reads the environment once. A fixed test
# secret keeps tokens independent of whatever is in a developer's backend/.env.
os.environ["AUTH_SECRET"] = "test-only-secret-with-at-least-32-characters"

import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session

from backend.db import candidates as candidate_store
from backend.db import users as user_store
from backend.db.engine import alembic_config, make_engine, set_engine
from backend.db.seed import seed
from backend.db.tables import User
from backend.security import create_access_token


def _url(path) -> str:
    return f"sqlite:///{path.as_posix()}"


@pytest.fixture(scope="session")
def _template_db(tmp_path_factory):
    path = tmp_path_factory.mktemp("db") / "template.db"
    command.upgrade(alembic_config(_url(path)), "head")
    engine = make_engine(_url(path))
    set_engine(engine)
    try:
        seed()
        # Fold the WAL into the main file so a plain file copy is complete.
        with engine.connect() as connection:
            connection.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))
    finally:
        engine.dispose()
        set_engine(None)
    return path


@pytest.fixture
def db(_template_db, tmp_path):
    path = tmp_path / "test.db"
    shutil.copy(_template_db, path)
    engine = make_engine(_url(path))
    set_engine(engine)
    yield engine
    engine.dispose()
    set_engine(None)


@pytest.fixture
def client(db):
    from backend.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(db):
    """`auth_headers("committee")` -> headers for a new committee member.
    `auth_headers("applicant", owns="c-003")` links the applicant to c-003."""

    def make(role: str, *, owns: str | None = None) -> dict[str, str]:
        # Tokens are minted directly, so the password hash is never checked.
        user = user_store.create_user(f"{role}-{uuid.uuid4().hex[:8]}@example.kz", "unused", role, role=role)
        if owns is not None:
            with Session(db) as session:
                row = session.get(User, user["id"])
                row.applicant_id = candidate_store.applicant_id_for(owns)
                session.add(row)
                session.commit()
        return {"Authorization": f"Bearer {create_access_token(user['id'], role)}"}

    return make
