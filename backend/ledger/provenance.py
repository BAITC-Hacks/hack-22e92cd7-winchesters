"""Where a stored ledger came from, in words a committee member can read (LED-12).

Only two things can put a ledger in the database: a cached pipeline run
(`python -m backend.ledger.cache`, loaded by `python -m backend.db init`) and
the LED-03 worked example that stands in for c-001 until a run is cached. The
example was written by hand for a fictional applicant, so none of its levels
or quotes are about the applicant it is attached to. Every view that shows a
ledger says which of the two it is, the way the Scenario Lab says "cached
demo transcript".

Nothing is stored for this: it is derived from `model_judge`, which the seed
sets to HAND_AUTHORED for the example.
"""

from __future__ import annotations

from typing import Any, Literal

from backend.ledger.schema import CandidateLedger

HAND_AUTHORED = "hand-authored"

Kind = Literal["illustrative_example", "cached_run"]

ILLUSTRATIVE_LABEL = "Illustrative worked example — not from this applicant"
ILLUSTRATIVE_DETAIL = (
    "Hand-authored for the LED-03 schema about a fictional applicant. Its levels and quotes, including the "
    "written-presentation quote, are not this applicant's; nothing here was scored."
)
CACHED_LABEL = "Cached ledger — built offline, not scored live"


def kind_of(ledger: CandidateLedger) -> Kind:
    return "illustrative_example" if ledger.model_judge == HAND_AUTHORED else "cached_run"


def describe(ledger: CandidateLedger) -> dict[str, Any]:
    """The provenance block the memo and pre-brief carry."""
    if kind_of(ledger) == "illustrative_example":
        return {"kind": "illustrative_example", "illustrative": True, "label": ILLUSTRATIVE_LABEL, "detail": ILLUSTRATIVE_DETAIL}
    return {
        "kind": "cached_run",
        "illustrative": False,
        "label": CACHED_LABEL,
        "detail": (
            f"Built once by {ledger.model_judge or 'an unrecorded model'} with prompt {ledger.prompt_version or 'unknown'} "
            "and loaded from the LED-12 cache; no model was called for this view."
        ),
    }
