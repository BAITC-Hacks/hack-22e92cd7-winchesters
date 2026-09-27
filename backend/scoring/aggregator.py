"""Score aggregation, ranking, and comparison utilities."""

from __future__ import annotations

from backend.models import (
    Candidate,
    CandidateScore,
    RankedCandidate,
    ScoringWeights,
)


def recompute_overall(score: CandidateScore, weights: ScoringWeights) -> float:
    """Recompute overall score with new weights."""
    weight_map = {
        "academic_strength": weights.academic_strength,
        "leadership_potential": weights.leadership_potential,
        "motivation_values": weights.motivation_values,
        "growth_trajectory": weights.growth_trajectory,
        "communication": weights.communication,
    }
    overall = sum(
        d.score * weight_map.get(d.dimension, 0.2)
        for d in score.dimensions
    )
    return round(overall, 1)


def rank_candidates(
    candidates: list[Candidate],
    scores: dict[str, CandidateScore],
    weights: ScoringWeights | None = None,
) -> list[RankedCandidate]:
    """Rank candidates by their overall AI score (or baseline if AI unavailable)."""
    if weights is None:
        weights = ScoringWeights()

    ranked: list[tuple[float, Candidate]] = []
    for c in candidates:
        s = scores.get(c.id)
        if s:
            overall = recompute_overall(s, weights)
            s.overall_score = overall
        else:
            overall = 0.0
        ranked.append((overall, c))

    ranked.sort(key=lambda x: x[0], reverse=True)

    return [
        RankedCandidate(
            rank=i + 1,
            candidate=c,
            ai_score=scores.get(c.id) if scores.get(c.id, None) and scores[c.id].scorer_type == "ai" else None,
            baseline_score=scores.get(c.id) if scores.get(c.id, None) and scores[c.id].scorer_type == "baseline" else None,
        )
        for i, (_, c) in enumerate(ranked)
    ]


def compare_scores(
    baseline: CandidateScore,
    ai: CandidateScore,
) -> dict:
    """Compare baseline vs AI scores for a candidate."""
    baseline_dims = {d.dimension: d for d in baseline.dimensions}
    ai_dims = {d.dimension: d for d in ai.dimensions}

    comparison = []
    for dim_name in baseline_dims:
        b = baseline_dims[dim_name]
        a = ai_dims.get(dim_name)
        comparison.append({
            "dimension": dim_name,
            "baseline_score": b.score,
            "ai_score": a.score if a else None,
            "difference": round(a.score - b.score, 1) if a else None,
            "baseline_explanation": b.explanation,
            "ai_explanation": a.explanation if a else "",
        })

    return {
        "candidate_id": baseline.candidate_id,
        "baseline_overall": baseline.overall_score,
        "ai_overall": ai.overall_score,
        "overall_difference": round(ai.overall_score - baseline.overall_score, 1),
        "dimensions": comparison,
        "baseline_recommendation": baseline.recommendation,
        "ai_recommendation": ai.recommendation,
    }
