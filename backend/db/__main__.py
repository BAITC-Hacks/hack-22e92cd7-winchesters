"""Database commands.

    python -m backend.db init    migrate to the latest schema, then load seed data
    python -m backend.db reset   delete the local SQLite file and run init again

Both are safe to repeat. `reset` refuses to touch anything but a SQLite file.
"""

from __future__ import annotations

import sys
from pathlib import Path

from alembic import command
from sqlalchemy.engine import make_url

from backend import settings
from backend.db.engine import alembic_config, get_engine
from backend.db.seed import seed


def init() -> None:
    command.upgrade(alembic_config(), "head")
    result = seed()
    print(
        f"schema at head; applicants: {result.applicants_added} added, "
        f"{result.applicants_total - result.applicants_added} already present"
        + ("; demo committee account created" if result.demo_user_added else "")
    )


def reset() -> None:
    url = make_url(settings.DATABASE_URL)
    if url.get_backend_name() != "sqlite" or not url.database:
        sys.exit(f"reset only deletes a local SQLite file; DATABASE_URL is {url.render_as_string()}")
    get_engine().dispose()
    for suffix in ("", "-wal", "-shm"):
        Path(url.database + suffix).unlink(missing_ok=True)
    print(f"deleted {url.database}")
    init()


COMMANDS = {"init": init, "reset": reset}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        sys.exit(__doc__)
    COMMANDS[sys.argv[1]]()
