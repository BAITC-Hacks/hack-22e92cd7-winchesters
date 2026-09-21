"""Database commands.

    python -m backend.db init    migrate to the latest schema, then load seed data
    python -m backend.db reset   delete the local SQLite file and run init again
    python -m backend.db create-user EMAIL ROLE "FULL NAME"
                                 add a staff account (interviewer | committee |
                                 admin); the password is asked for, never passed
                                 on the command line

init and reset are safe to repeat. `reset` refuses to touch anything but a SQLite file.
"""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

from alembic import command
from sqlalchemy.engine import make_url

from backend import settings
from backend.db.engine import alembic_config, get_engine
from backend.db import users
from backend.db.seed import seed
from backend.security import STAFF_ROLES, hash_password


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


def create_user(email: str, role: str, full_name: str) -> None:
    # Applicants register themselves through the API; this is for staff only.
    if role not in STAFF_ROLES:
        sys.exit(f"role must be one of: {', '.join(STAFF_ROLES)}")
    password = getpass.getpass("password (min 8 characters): ")
    if len(password) < 8:
        sys.exit("password too short")
    if getpass.getpass("repeat password: ") != password:
        sys.exit("passwords do not match")
    try:
        user = users.create_user(email.strip().lower(), hash_password(password), full_name, role=role)
    except users.EmailTaken:
        sys.exit(f"{email} already has an account")
    print(f"created {user['role']} {user['email']}")


COMMANDS = {"init": (init, 0), "reset": (reset, 0), "create-user": (create_user, 3)}

if __name__ == "__main__":
    command_name = sys.argv[1] if len(sys.argv) > 1 else ""
    if command_name not in COMMANDS or len(sys.argv) - 2 != COMMANDS[command_name][1]:
        sys.exit(__doc__)
    COMMANDS[command_name][0](*sys.argv[2:])
