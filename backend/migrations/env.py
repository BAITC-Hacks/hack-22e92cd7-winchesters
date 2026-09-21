"""Alembic environment.

Three SQLite specifics matter here:

- `render_as_batch=True`: SQLite cannot ALTER most things, so Alembic rebuilds
  the table (copy, drop, rename). Without batch mode any later column change
  fails.
- Migrations connect *without* `PRAGMA foreign_keys=ON`, unlike the app. A
  batch rebuild drops the old table, and with foreign keys on, SQLite runs the
  ON DELETE CASCADE actions for that drop: rebuilding `applicants` would
  silently delete every artifact.
- Batch rebuilds also drop the table's triggers, which is how the append-only
  tables are enforced. Every online migration ends by checking they are all
  still there (`_require_append_only_triggers`), inside one transaction that
  also covers the DDL (`_sqlite_transactional_ddl`), so a failure rolls the
  whole upgrade back.
"""

from __future__ import annotations

from alembic import context
from sqlalchemy import create_engine, event, pool
from sqlmodel import SQLModel

from backend import settings
import backend.db.tables  # noqa: F401  (registers the tables on SQLModel.metadata)
from backend.db.engine import missing_append_only_triggers

config = context.config
target_metadata = SQLModel.metadata


def _url() -> str:
    return config.get_main_option("sqlalchemy.url") or settings.DATABASE_URL


def run_migrations_offline() -> None:
    context.configure(
        url=_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _sqlite_transactional_ddl(engine) -> None:
    """Run DDL inside the transaction, so a failed migration leaves nothing.

    The sqlite3 driver only opens a transaction before INSERT/UPDATE/DELETE, so
    CREATE, DROP and ALTER are committed as they run. A migration that fails
    halfway (including on the trigger check below) would stay half-applied and
    stamped as done. The recipe from the SQLAlchemy SQLite docs: take the
    driver out of transaction handling and emit BEGIN ourselves.
    """

    @event.listens_for(engine, "connect")
    def _no_driver_transactions(dbapi_connection, _record) -> None:
        dbapi_connection.isolation_level = None

    @event.listens_for(engine, "begin")
    def _begin(connection) -> None:
        connection.exec_driver_sql("BEGIN")


def run_migrations_online() -> None:
    connectable = create_engine(_url(), poolclass=pool.NullPool)
    if connectable.dialect.name == "sqlite":
        _sqlite_transactional_ddl(connectable)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
            transactional_ddl=True,
        )
        with context.begin_transaction():
            context.run_migrations()
            _require_append_only_triggers(connection)


def _require_append_only_triggers(connection) -> None:
    """Fail the migration if a batch rebuild dropped an append-only trigger.

    Batch mode rebuilds a table by copy, drop, rename, and SQLite drops the
    old table's triggers with it. Alembic does not know about them, so without
    this check a later migration touching evidence_items would quietly make it
    editable again. The fix is to recreate the triggers at the end of that
    migration (their SQL is in revision 0003).
    """
    missing = missing_append_only_triggers(connection)
    if missing:
        raise RuntimeError(
            "migration left append-only tables without their triggers: "
            + ", ".join(missing)
            + ". A batch rebuild drops triggers; recreate them in the migration (see revision 0003)."
        )


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
