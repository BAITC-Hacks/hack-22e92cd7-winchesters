"""Cached evidence ledgers for the demo applicants (task LED-12).

The demo must never wait on a model. This module runs the LED-04 pipeline once
per applicant, offline, and writes each result to `fixtures/cache/<ref>.json`.
`python -m backend.db init` then loads those files into the database, and every
demo click reads the stored snapshot.

    python -m backend.ledger.cache                 build every applicant without a file
    python -m backend.ledger.cache --only c-001,c-002
    python -m backend.ledger.cache --force         rebuild files that already exist

Needs ANTHROPIC_API_KEY (backend/.env) and an initialised database. A run where
every AI-rated competency came back empty is treated as a failed call and not
written: an outage must not be cached as "no evidence".
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from backend.ledger.schema import CandidateLedger

CACHE_DIR = Path(__file__).resolve().parent / "fixtures" / "cache"


def cache_path(ref: str, cache_dir: Path = CACHE_DIR) -> Path:
    return cache_dir / f"{ref}.json"


def cached_refs(cache_dir: Path = CACHE_DIR) -> list[str]:
    return sorted(path.stem for path in cache_dir.glob("*.json")) if cache_dir.is_dir() else []


def read_cached(ref: str, cache_dir: Path = CACHE_DIR) -> CandidateLedger:
    return CandidateLedger.model_validate(json.loads(cache_path(ref, cache_dir).read_text(encoding="utf-8")))


def write_cached(ledger: CandidateLedger, cache_dir: Path = CACHE_DIR) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_path(ledger.applicant_ref, cache_dir)
    path.write_text(json.dumps(ledger.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def looks_failed(ledger: CandidateLedger) -> bool:
    """True when every competency the AI may rate is the pipeline's empty fallback."""
    from backend.ledger.pipeline import empty_rating
    from backend.ledger.rubric import RUBRIC

    rateable = [rating for rating in ledger.competencies if not rating.reserved_for_humans]
    return bool(rateable) and all(rating == empty_rating(RUBRIC[rating.competency]) for rating in rateable)


async def build(refs: list[str] | None = None, force: bool = False, cache_dir: Path = CACHE_DIR) -> dict[str, str]:
    """Build and cache ledgers; returns ref -> outcome (written, skipped, failed, missing)."""
    from backend.db.candidates import get_candidate, list_candidates
    from backend.ledger.pipeline import build_ledger

    pairs = [(c.id, c) for c in list_candidates()] if refs is None else [(ref, get_candidate(ref)) for ref in refs]
    outcomes: dict[str, str] = {}
    for ref, candidate in pairs:
        if candidate is None:
            outcomes[ref] = "missing"
        elif cache_path(ref, cache_dir).exists() and not force:
            outcomes[ref] = "skipped"
        else:
            ledger = await build_ledger(candidate)
            ledger.applicant_ref = ref
            if looks_failed(ledger):
                outcomes[ref] = "failed"
            else:
                write_cached(ledger, cache_dir)
                outcomes[ref] = "written"
        print(f"{ref}: {outcomes[ref]}", flush=True)
    return outcomes


def main(argv: list[str] | None = None) -> int:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    parser = argparse.ArgumentParser(prog="python -m backend.ledger.cache", description=__doc__.split("\n\n")[0])
    parser.add_argument("--only", help="comma-separated applicant refs, e.g. c-001,c-002")
    parser.add_argument("--force", action="store_true", help="rebuild files that already exist")
    args = parser.parse_args(argv)
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set (backend/.env); nothing was built.", file=sys.stderr)
        return 2
    refs = [ref.strip() for ref in args.only.split(",") if ref.strip()] if args.only else None
    outcomes = asyncio.run(build(refs, force=args.force))
    failed = [ref for ref, outcome in outcomes.items() if outcome in ("failed", "missing")]
    print(f"{sum(o == 'written' for o in outcomes.values())} written, {len(failed)} failed or missing")
    if any(o == "written" for o in outcomes.values()):
        print("load them with: python -m backend.db init")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
