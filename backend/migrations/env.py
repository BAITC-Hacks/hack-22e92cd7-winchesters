"""Alembic environment.

Two SQLite specifics matter here:

- `render_as_batch=True`: SQLite cannot ALTER most things, so Alembic rebuilds
  the table (copy, drop, rename). Without batch mode any later column change
  fails.
- Migrations connect *without* `PRAGMA foreign_keys=ON`, unlike the app. A
  batch rebuild drops the old table, and with foreign keys on, SQLite runs the
  ON DELETE CASCADE actions for that drop: rebuilding `applicants` would
  silently delete every artifact.
"""

from __future__ import annotations

from alembic import context
from sqlalchemy import create_engine, pool
from sqlmodel import SQLModel

from backend import settings
import backend.db.tables  # noqa: F401  (registers the tables on SQLModel.metadata)

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


def run_migrations_online() -> None:
    connectable = create_engine(_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
