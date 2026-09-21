"""Engine construction and the schema-at-head check.

Synchronous SQLAlchemy by design (docs/plan/production-readiness.md § Async
vision): `def` routes are threadpooled by FastAPI, and `async def` routes call
the repository through `run_in_threadpool`, so a DB call never blocks the event
loop.
"""

from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import event, text
from sqlalchemy.engine import Connection, Engine
from sqlmodel import create_engine

from backend import settings
from backend.db.tables import APPEND_ONLY_TABLES, append_only_trigger_names

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"

_engine: Engine | None = None


def make_engine(url: str) -> Engine:
    if not url.startswith("sqlite"):
        return create_engine(url, pool_pre_ping=True)

    # FastAPI hands requests to a threadpool, so one connection can be used
    # from a thread other than the one that opened it.
    engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _record) -> None:
        cursor = dbapi_connection.cursor()
        # SQLite ignores foreign keys unless asked, per connection. Without
        # this every FK in the schema is decoration.
        cursor.execute("PRAGMA foreign_keys=ON")
        # Readers do not block on a writer: the dashboard keeps loading while a
        # scoring run saves results.
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    return engine


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = make_engine(settings.DATABASE_URL)
    return _engine


def set_engine(engine: Engine | None) -> None:
    """Point the app at a different database. Tests use this; nothing else should."""
    global _engine
    _engine = engine


def alembic_config(url: str | None = None) -> Config:
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(REPO_ROOT / "backend" / "migrations"))
    config.set_main_option("sqlalchemy.url", url or settings.DATABASE_URL)
    return config


class SchemaNotCurrent(RuntimeError):
    pass


def missing_append_only_triggers(connection: Connection) -> list[str]:
    """Trigger names an existing append-only table should have and does not.

    A batch-mode rebuild copies a table, drops the old one and renames the
    copy; the triggers go with the dropped table and nothing recreates them.
    Tables that do not exist (a downgrade below the revision that created
    them) are skipped. SQLite only: elsewhere append-only is a different
    mechanism, and this returns nothing.
    """
    if connection.dialect.name != "sqlite":
        return []
    rows = connection.execute(
        text("SELECT type, name FROM sqlite_master WHERE type IN ('table', 'trigger')")
    ).all()
    tables = {name for kind, name in rows if kind == "table"}
    triggers = {name for kind, name in rows if kind == "trigger"}
    return [
        name
        for table in APPEND_ONLY_TABLES
        if table in tables
        for name in append_only_trigger_names(table)
        if name not in triggers
    ]


def assert_schema_current(engine: Engine | None = None) -> None:
    """Fail at startup, with the fix in the message, if migrations were not run.

    The alternative is the first request failing with "no such table", which
    tells a teammate nothing about what to do.
    """
    engine = engine or get_engine()
    head = ScriptDirectory.from_config(alembic_config()).get_current_head()
    with engine.connect() as connection:
        current = MigrationContext.configure(connection).get_current_revision()
    if current != head:
        raise SchemaNotCurrent(
            f"Database schema is at {current or 'nothing'}, code expects {head}. "
            "Run: python -m backend.db init"
        )
