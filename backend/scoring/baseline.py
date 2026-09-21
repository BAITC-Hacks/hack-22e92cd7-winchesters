"""The rule-based reference, rewritten to measure evidence, not merit (LED-01).

What this used to be: a scorer that awarded points for GPA on a four-point
scale, for counting English keywords in the essay, for writing between 400 and
800 words, and for a growth delta computed from a school-type advantage table.
Every one of those is either something the client says does not measure
leadership, or a penalty on applicants who write in Kazakh, or a score computed
from background.

What it is now: a statement of how much material exists to assess each
dimension. That is genuinely useful, because the committee needs to know the
difference between a candidate who was assessed on four sources and one who was
assessed on an essay alone, and because it gives the AI pipeline something
honest to be compared against.

It is not a judgement of the candidate, and the explanations say so on every
dimension. The committee-facing assessment comes from the evidence ledger in
`backend/ledger/` (task LED-04), which rates behaviour against the client's own
BARS anchors.
"""

from __future__ import annotations

from backend.models import (
    Candidate,
    CandidateScore,
    Confidence,
    DimensionScore,
    ScoringWeights,
)
from backend.scoring.signal_extractor import ExtractedSignals, extract_signals

NOT_A_MERIT_JUDGEMENT = (
    "Data sufficiency, not an assessment of the candidate. It reports how much "
    "material exists to assess this dimension."
)


def _sufficiency(present: list[tuple[str, bool]]) -> tuple[float, list[str], list[str]]:
    """Turn a checklist of available inputs into a score and two lists.

    Returns the percentage present, the labels that are present, and the labels
    that are missing. Anything absent is reported as a gap to fill, never as a
    negative judgement of the applicant.
    """
    if not present:
        return (0.0, [], [])
    have = [label for label, exists in present if exists]
    missing = [label for label, exists in present if not exists]
    return (round(len(have) / len(present) * 100, 1), have, missing)


def _confidence_for(score: float) -> Confidence:
    if score >= 75:
        return Confidence.HIGH
    if score >= 40:
        return Confidence.MEDIUM
    return Confidence.LOW


def _dimension(name: str, checklist: list[tuple[str, bool]]) -> DimensionScore:
    """Build one dimension from a checklist of inputs that exist."""
    score, have, missing = _sufficiency(checklist)
    return DimensionScore(
        dimension=name,
        score=score,
        confidence=_confidence_for(score),
        explanation=(
            f"{NOT_A_MERIT_JUDGEMENT} Present: {', '.join(have) or 'nothing'}."
            + (f" Missing: {', '.join(missing)}." if missing else "")
        ),
        positive_factors=[f"{label} available" for label in have],
        concerns=[f"{label} not available" for label in missing],
    )


def _checklists(signals: ExtractedSignals) -> dict[str, list[tuple[str, bool]]]:
    """What counts as an input for each dimension.

    Keyed by dimension name for O(1) lookup and so the mapping is readable in
    one place rather than spread across five near-identical functions.
    """
    facts = signals.facts
    sources = signals.availability
    return {
        "academic_strength": [
            ("listed achievements", facts.achievement_count > 0),
            ("listed skills", bool(facts.skills)),
            ("essay", sources.has_essay),
        ],
        "leadership_potential": [
            ("extracurricular roles", bool(facts.roles)),
            ("projects", facts.project_count > 0),
            ("projects with described impact", bool(facts.projects_with_described_impact)),
            ("essay", sources.has_essay),
        ],
        "motivation_values": [
            ("essay", sources.has_essay),
            ("interview transcript", sources.has_interview),
            ("recommendation letter", sources.has_recommendation),
        ],
        "growth_trajectory": [
            ("activities sustained two years or more", bool(facts.sustained_activities)),
            ("projects", facts.project_count > 0),
            ("essay", sources.has_essay),
            ("interview transcript", sources.has_interview),
        ],
        "communication": [
            ("essay", sources.has_essay),
            ("interview transcript", sources.has_interview),
            ("video transcript", sources.has_video_transcript),
        ],
    }


def compute_baseline_score(
    candidate: Candidate,
    weights: ScoringWeights | None = None,
) -> CandidateScore:
    """Report how well-evidenced this application is, dimension by dimension."""
    applied = weights or ScoringWeights()
    signals = extract_signals(candidate)
    dimensions = [_dimension(name, checklist) for name, checklist in _checklists(signals).items()]

    weight_map = {
        "academic_strength": applied.academic_strength,
        "leadership_potential": applied.leadership_potential,
        "motivation_values": applied.motivation_values,
        "growth_trajectory": applied.growth_trajectory,
        "communication": applied.communication,
    }
    overall = round(sum(d.score * weight_map.get(d.dimension, 0.2) for d in dimensions), 1)

    missing = signals.availability.missing()
    return CandidateScore(
        candidate_id=candidate.id,
        dimensions=dimensions,
        overall_score=overall,
        # Always the neutral value, for every applicant. This reference measures
        # how complete a file is, so it has no opinion on anybody, and a badge
        # reading "Recommend" because four sources were uploaded would be a
        # merit claim the number does not support. The old scorer derived this
        # from thresholds of 70 and 50 that nobody had calibrated against
        # anything. Real recommendations come from the evidence ledger under the
        # committee's own weights and cut-offs (tasks LED-04 and COM-01).
        recommendation="consider",
        summary=(
            f"Evidence completeness {overall}/100. "
            + (f"Missing sources: {', '.join(missing)}. " if missing else "All four sources present. ")
            + "This reference reports how much material exists to assess, and makes no "
            "recommendation about any candidate."
        ),
        scorer_type="baseline",
    )
