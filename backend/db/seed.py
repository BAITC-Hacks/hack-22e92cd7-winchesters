"""Load the 16 demo applicants and, under DEMO_MODE, the committee demo account.

Idempotent: records already present (matched by their `c-###` id, or by email
for users) are skipped, so `python -m backend.db init` is safe to rerun.
`backend/data/candidates.json` is now seed input only; nothing writes to it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from sqlmodel import Session, select

from backend import settings
from backend.db.candidates import import_candidate
from backend.db.engine import get_engine
from backend.db.tables import User
from backend.models import Candidate

SEED_FILE = Path(__file__).resolve().parents[1] / "data" / "candidates.json"

DEMO_COMMITTEE_EMAIL = "committee@invisionu.edu"
DEMO_COMMITTEE_PASSWORD = "demo2026"


@dataclass
class SeedResult:
    applicants_added: int
    applicants_total: int
    demo_user_added: bool


def seed() -> SeedResult:
    # The hashing scheme belongs to the auth router until FND-05 replaces it;
    # imported here, not at module level, so the db package does not depend on
    # routers at import time.
    from backend.routers.auth import hash_password

    records = [Candidate(**raw) for raw in json.loads(SEED_FILE.read_text(encoding="utf-8"))]

    with Session(get_engine()) as session:
        added = sum(import_candidate(session, record) for record in records)

        demo_user_added = False
        if settings.DEMO_MODE:
            exists = session.exec(select(User).where(User.email == DEMO_COMMITTEE_EMAIL)).first()
            if exists is None:
                session.add(
                    User(
                        email=DEMO_COMMITTEE_EMAIL,
                        full_name="Admissions Committee",
                        password_hash=hash_password(DEMO_COMMITTEE_PASSWORD),
                        role="committee",
                    )
                )
                demo_user_added = True

        session.commit()

    return SeedResult(applicants_added=added, applicants_total=len(records), demo_user_added=demo_user_added)
