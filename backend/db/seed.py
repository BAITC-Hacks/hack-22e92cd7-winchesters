"""Load the 16 demo applicants and, under DEMO_MODE, the committee demo account.

Idempotent: records already present (matched by their `c-###` id, or by email
for users) are skipped, so `python -m backend.db init` is safe to rerun. The
one exception is the demo committee account: if its stored password no longer
verifies (a database created before FND-05 kept an unsalted SHA-256 hash that
argon2 rejects, so the documented login answered 401) or its role drifted, the
row is repaired in place.
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
from backend.security import Role, hash_password, verify_password

SEED_FILE = Path(__file__).resolve().parents[1] / "data" / "candidates.json"

DEMO_COMMITTEE_EMAIL = "committee@invisionu.edu"
DEMO_COMMITTEE_PASSWORD = "demo2026"


@dataclass
class SeedResult:
    applicants_added: int
    applicants_total: int
    demo_user_added: bool
    demo_user_repaired: bool = False


def seed() -> SeedResult:
    records = [Candidate(**raw) for raw in json.loads(SEED_FILE.read_text(encoding="utf-8"))]

    with Session(get_engine()) as session:
        added = sum(import_candidate(session, record) for record in records)

        demo_user_added = demo_user_repaired = False
        if settings.DEMO_MODE:
            exists = session.exec(select(User).where(User.email == DEMO_COMMITTEE_EMAIL)).first()
            if exists is None:
                session.add(
                    User(
                        email=DEMO_COMMITTEE_EMAIL,
                        full_name="Admissions Committee",
                        password_hash=hash_password(DEMO_COMMITTEE_PASSWORD),
                        role=Role.COMMITTEE.value,
                    )
                )
                demo_user_added = True
            else:
                # Verify first, so a healthy row is left byte-for-byte alone.
                if not verify_password(exists.password_hash, DEMO_COMMITTEE_PASSWORD):
                    exists.password_hash = hash_password(DEMO_COMMITTEE_PASSWORD)
                    demo_user_repaired = True
                if exists.role != Role.COMMITTEE.value:
                    exists.role = Role.COMMITTEE.value
                    demo_user_repaired = True
                if demo_user_repaired:
                    session.add(exists)

        session.commit()

    return SeedResult(
        applicants_added=added,
        applicants_total=len(records),
        demo_user_added=demo_user_added,
        demo_user_repaired=demo_user_repaired,
    )


WORKED_EXAMPLE = Path(__file__).resolve().parents[1] / "ledger" / "fixtures" / "ledger_example.json"
WORKED_EXAMPLE_REF = "c-001"


def _canonical(ledger) -> str:
    body = ledger.model_dump(mode="json")
    body["competencies"] = sorted(body["competencies"], key=lambda c: c["competency"])
    for competency in body["competencies"]:
        competency["indicators"] = sorted(competency["indicators"], key=lambda i: i["indicator_id"])
        for indicator in competency["indicators"]:
            for item in indicator["evidence"]:
                item["source_ref"] = ""  # an artifact FK in the database, not stored from the cache
    return json.dumps(body, sort_keys=True, ensure_ascii=False)


def seed_demo_ledger(cache_dir: Path | None = None) -> int:
    """Load the cached LED-12 ledgers into the demo database; returns how many were saved.

    A cached file is saved when the stored snapshot differs from it, so rerunning
    init is a no-op and a rebuilt cache replaces an older snapshot. c-001 falls
    back to the hand-authored LED-03 worked example, labelled as such, until a
    real run for it is cached.
    """
    from backend.db import ledger as ledger_store
    from backend.db.candidates import applicant_id_for
    from backend.ledger import cache
    from backend.ledger.provenance import HAND_AUTHORED
    from backend.ledger.schema import CandidateLedger

    cache_dir = cache.CACHE_DIR if cache_dir is None else cache_dir
    saved = 0
    for ref in cache.cached_refs(cache_dir):
        if applicant_id_for(ref) is None:
            continue
        ledger = cache.read_cached(ref, cache_dir)
        ledger.applicant_ref = ref
        stored = ledger_store.load_ledger(ref)
        if stored is None or _canonical(stored) != _canonical(ledger):
            ledger_store.save_ledger(ref, ledger)
            saved += 1
    if WORKED_EXAMPLE_REF not in cache.cached_refs(cache_dir) and not ledger_store.has_ledger(WORKED_EXAMPLE_REF):
        example = CandidateLedger.model_validate(json.loads(WORKED_EXAMPLE.read_text(encoding="utf-8")))
        # Hand-authored for a fictional applicant, not a model run: every view
        # labels it "illustrative, not from this applicant" (backend/ledger/provenance.py).
        example.model_judge = example.model_extract = HAND_AUTHORED
        example.prompt_version = "led-03-worked-example"
        ledger_store.save_ledger(WORKED_EXAMPLE_REF, example)
        saved += 1
    return saved
