"""The approved, score-free COM-06 interviewer probe bank.

The bank is a projection of the extended-methodology P4 contract: canonical
ATOLA questions are owned by ``backend.ledger.atola`` and the allowed
competency-specific paraphrases are selected here. It is deliberately kept
outside the scoring pipeline and its hash covers only the immutable payload.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from backend.ledger import atola
from backend.ledger.rubric import COMPETENCY_ORDER
from backend.ledger.schema import AtolaComponent, Competency

PROBE_BANK_VERSION = "com-06-extended-1.0"
PROBE_BANK_SOURCE = "docs/research/agent_methodology.md#P4"

_PARAPHRASES: dict[AtolaComponent, tuple[str, str]] = {
    AtolaComponent.ACTION: (
        "Please walk me through the specific steps you took in that situation.",
        "What did you personally do first, next, and after that?",
    ),
    AtolaComponent.THINKING: (
        "What options did you consider, and why did you choose that approach?",
        "What was your reasoning when you decided how to handle it?",
    ),
    AtolaComponent.OUTCOME: (
        "What changed as a result, and how did you know?",
        "What was the outcome and how could it be measured?",
    ),
    AtolaComponent.LEARNINGS: (
        "What did you learn from that experience?",
        "What would you carry forward from this experience?",
    ),
    AtolaComponent.APPLICATION: (
        "Tell me about another situation where you applied that learning.",
        "Where else have you used the lesson from this experience?",
    ),
}


def _payload() -> list[dict[str, Any]]:
    return [
        {
            "probe_id": f"{competency.value}.{component.value}",
            "competency": competency.value,
            "missing_atola_component": component.value,
            "canonical": atola.PROBE_FOR_MISSING[component],
            "allowed_paraphrases": list(_PARAPHRASES[component]),
            "methodology_source": PROBE_BANK_SOURCE,
            "approval_status": "approved_for_committee_prebrief",
            "leak_guard": {
                "candidate_facing": False,
                "public_item_ids": [],
                "checks": ["exact_ngram", "embedding_similarity"],
            },
        }
        for competency in COMPETENCY_ORDER
        for component in atola.ATOLA_SEQUENCE
    ]


PROBE_BANK: tuple[dict[str, Any], ...] = tuple(_payload())
_HASH_PAYLOAD = json.dumps(PROBE_BANK, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
PROBE_BANK_HASH = hashlib.sha256(_HASH_PAYLOAD.encode("utf-8")).hexdigest()

PROBE_BANK_PROVENANCE = {
    "version": PROBE_BANK_VERSION,
    "content_hash": f"sha256:{PROBE_BANK_HASH}",
    "source": PROBE_BANK_SOURCE,
    "entry_count": len(PROBE_BANK),
    "selection_key": "competency x missing ATOLA component",
    "score_path_unchanged": True,
    "live_rebuild": False,
}

_BY_KEY = {
    (item["competency"], item["missing_atola_component"]): item
    for item in PROBE_BANK
}


def probe_for(competency: Competency, component: AtolaComponent) -> dict[str, Any]:
    """Return a serializable bank record for one missing component."""
    return dict(_BY_KEY[(competency.value, component.value)])