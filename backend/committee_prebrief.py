"""Build the persisted-ledger interviewer pre-brief (COM-06).

This module is deliberately a projection: it never calls the scoring pipeline
and never exposes a level. The probe bank is versioned separately so the
extended methodology (LED-13) can replace it without changing the response contract.
"""

from __future__ import annotations

from typing import Any

from backend.committee_probe_bank import PROBE_BANK_PROVENANCE, probe_for
from backend.ledger import atola
from backend.ledger.schema import CandidateLedger, Competency, EvidenceStatus

PROBE_BANK_VERSION = PROBE_BANK_PROVENANCE["version"]


def _probe(competency: Competency, component: atola.AtolaComponent) -> dict[str, Any]:
    bank_probe = probe_for(competency, component)
    return {
        **bank_probe,
        "paraphrase": bank_probe["allowed_paraphrases"][0],
    }


def _evidence(rating: Any) -> list[Any]:
    return [item for indicator in rating.indicators for item in indicator.evidence]


def _state(rating: Any | None) -> str:
    if rating is None:
        return "not_in_ledger"
    if rating.reserved_for_humans:
        return "live_only"
    verified = [item for item in _evidence(rating) if item.verified]
    if not verified:
        return "no_evidence"
    return "demonstrated" if any(item.status is EvidenceStatus.PRESENT for item in verified) else "claimed_only"


def build_prebrief(ledger: CandidateLedger) -> dict[str, Any]:
    """Return a score-free pre-brief from one persisted ledger snapshot."""
    rows: list[dict[str, Any]] = []
    strengths: list[dict[str, Any]] = []
    for rating in sorted(ledger.competencies, key=lambda item: item.competency.value):
        evidence = _evidence(rating)
        demonstrated = [item for item in evidence if item.verified and item.status is EvidenceStatus.PRESENT]
        strengths.extend(
            {"competency": rating.competency.value, "quote": item.quote, "source": item.source.value}
            for item in demonstrated
        )
        missing = atola.components_missing(evidence)
        selected = None if rating.reserved_for_humans or not missing else _probe(rating.competency, missing[0])
        discrepancies = [
            flag.model_dump(mode="json")
            for flag in rating.flags
            if flag.code.startswith("discrepancy") or "contradict" in flag.code or "conflict" in flag.explanation.lower()
        ]
        rows.append({
            "competency": rating.competency.value,
            "evidence_state": _state(rating),
            "missing_components": [component.value for component in missing],
            "probe": selected,
            "discrepancy_alerts": discrepancies,
        })

    return {
        "candidate_id": ledger.applicant_ref,
        "probe_bank": PROBE_BANK_PROVENANCE,
        "probe_bank_version": PROBE_BANK_VERSION,
        "score_withheld": True,
        "strengths": strengths[:2],
        "rows": rows,
    }