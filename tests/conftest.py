"""Shared fixtures.

`db` gives each test its own SQLite file with the real migrations applied and
the seed loaded. Migrating once per session and copying the file per test keeps
that fast, and running the actual Alembic migrations here means CI fails on a
broken migration, not just on broken code.
"""

from __future__ import annotations

import shutil

import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.db.engine import alembic_config, make_engine, set_engine
from backend.db.seed import seed


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
