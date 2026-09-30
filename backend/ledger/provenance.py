"""Where a stored ledger came from, in words a committee member can read (LED-12).

Three things can put a ledger in the database: a cached pipeline run
(`python -m backend.ledger.cache`, loaded by `python -m backend.db init`), the
demo-mode stand-in used while no model key is set (`demo.py`), and the LED-03
worked example that stands in for c-001 when neither exists. The
example was written by hand for a fictional applicant, so none of its levels
or quotes are about the applicant it is attached to. Every view that shows a
ledger says which of the two it is, the way the Scenario Lab says "cached
demo transcript".

Nothing is stored for this: it is derived from `model_judge`, which the seed
sets to HAND_AUTHORED for the example and demo mode prefixes with DEMO_PREFIX.
"""

from __future__ import annotations

from typing import Any, Literal

from backend.ledger.schema import CandidateLedger

HAND_AUTHORED = "hand-authored"
DEMO_PREFIX = "demo-"

Kind = Literal["illustrative_example", "demo_mode", "cached_run"]

ILLUSTRATIVE_LABEL = "Illustrative worked example — not from this applicant"
ILLUSTRATIVE_DETAIL = (
    "Hand-authored for the LED-03 schema about a fictional applicant. Its levels and quotes, including the "
    "written-presentation quote, are not this applicant's; nothing here was scored."
)
CACHED_LABEL = "Cached ledger — built offline, not scored live"
DEMO_LABEL = "Demo mode · no live model"
DEMO_DETAIL = (
    "Built without a model key: a stand-in replaced the two model calls. The quotes are this applicant's own "
    "words, checked against their documents, and levels follow the same rules as a model run."
)


def kind_of(ledger: CandidateLedger) -> Kind:
    if ledger.model_judge == HAND_AUTHORED:
        return "illustrative_example"
    return "demo_mode" if ledger.model_judge.startswith(DEMO_PREFIX) else "cached_run"


def describe(ledger: CandidateLedger) -> dict[str, Any]:
    """The provenance block the memo and pre-brief carry."""
    kind = kind_of(ledger)
    if kind == "illustrative_example":
        return {"kind": "illustrative_example", "illustrative": True, "label": ILLUSTRATIVE_LABEL, "detail": ILLUSTRATIVE_DETAIL}
    if kind == "demo_mode":
        return {"kind": "demo_mode", "illustrative": False, "label": DEMO_LABEL, "detail": DEMO_DETAIL}
    return {
        "kind": "cached_run",
        "illustrative": False,
        "label": CACHED_LABEL,
        "detail": (
            f"Built once by {ledger.model_judge or 'an unrecorded model'} with prompt {ledger.prompt_version or 'unknown'} "
            "and loaded from the LED-12 cache; no model was called for this view."
        ),
    }
