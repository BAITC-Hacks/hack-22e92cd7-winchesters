"""Scoring and ranking endpoints.

Committee and admin only (FND-05): the whole router carries the guard.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool

from backend.models import CandidateScore, CommitteeOverride, RankedCandidate, ScoringWeights
from backend.routers.candidates import get_candidate_or_404, load_candidates
from backend.routers.guards import require_role
from backend.scoring.aggregator import compare_scores, rank_candidates, recompute_overall
from backend.scoring.ai_scorer import compute_ai_score
from backend.scoring.baseline import compute_baseline_score
from backend.security import Role

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/scoring",
    tags=["scoring"],
    dependencies=[Depends(require_role(Role.COMMITTEE, Role.ADMIN))],
)

# In-memory score cache (per session)
_score_cache: dict[str, CandidateScore] = {}
_baseline_cache: dict[str, CandidateScore] = {}


@router.post("/baseline/{candidate_id}", response_model=CandidateScore)
def score_baseline(candidate_id: str, weights: ScoringWeights | None = None):
    """Compute baseline (rule-based) score for a candidate."""
    candidate = get_candidate_or_404(candidate_id)
    score = compute_baseline_score(candidate, weights)
    _baseline_cache[candidate_id] = score
    return score


@router.post("/baseline/all", response_model=list[CandidateScore])
def score_all_baseline(weights: ScoringWeights | None = None):
    """Compute baseline scores for all candidates."""
    candidates = load_candidates()
    scores = []
    for c in candidates:
        score = compute_baseline_score(c, weights)
        _baseline_cache[c.id] = score
        scores.append(score)
    return scores


@router.post("/ai/{candidate_id}", response_model=CandidateScore)
async def score_ai(candidate_id: str, weights: ScoringWeights | None = None):
    """Compute AI-powered score for a candidate (uses Claude API)."""
    candidate = await run_in_threadpool(get_candidate_or_404, candidate_id)
    try:
        score = await compute_ai_score(candidate, weights)
        _score_cache[candidate_id] = score
        return score
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI scoring failed: {str(e)}")


@router.post("/ai/all", response_model=list[CandidateScore])
async def score_all_ai(weights: ScoringWeights | None = None):
    """Compute AI scores for all candidates.

    Candidates are scored concurrently; the shared semaphore in `backend.llm`
    caps how many calls are open at once. A candidate whose run fails is left
    out of the result and out of the cache rather than returned with a zero: a
    zero sorts to the bottom of the ranking, so an API timeout used to look
    exactly like a weak application.
    """
    candidates = await run_in_threadpool(load_candidates)
    results = await asyncio.gather(
        *(compute_ai_score(c, weights) for c in candidates),
        return_exceptions=True,
    )

    scores = []
    for candidate, result in zip(candidates, results):
        if isinstance(result, BaseException):
            logger.error("AI scoring failed for %s: %s", candidate.id, result)
            continue
        _score_cache[candidate.id] = result
        scores.append(result)
    return scores


@router.post("/rank", response_model=list[RankedCandidate])
def rank_all(weights: ScoringWeights | None = None, scorer: str = "baseline"):
    """Rank all candidates. Use scorer='baseline' or 'ai'."""
    candidates = load_candidates()
    cache = _score_cache if scorer == "ai" else _baseline_cache

    # Auto-compute baseline if cache empty
    if scorer == "baseline" and not _baseline_cache:
        for c in candidates:
            _baseline_cache[c.id] = compute_baseline_score(c, weights)
        return rank_candidates(candidates, _baseline_cache, weights)

    return rank_candidates(candidates, cache, weights)


@router.get("/compare/{candidate_id}")
def compare(candidate_id: str):
    """Compare baseline vs AI scores for a candidate."""
    baseline = _baseline_cache.get(candidate_id)
    ai = _score_cache.get(candidate_id)
    if not baseline:
        candidate = get_candidate_or_404(candidate_id)
        baseline = compute_baseline_score(candidate)
        _baseline_cache[candidate_id] = baseline
    if not ai:
        raise HTTPException(
            status_code=404,
            detail="AI score not yet computed. Run /api/scoring/ai/{id} first.",
        )
    return compare_scores(baseline, ai)


@router.post("/override", response_model=CandidateScore)
def override_score(override: CommitteeOverride):
    """Apply a committee override to a specific dimension score."""
    cid = override.candidate_id
    # Try AI cache first, then baseline
    score = _score_cache.get(cid) or _baseline_cache.get(cid)
    if not score:
        # Auto-compute baseline
        candidate = get_candidate_or_404(cid)
        score = compute_baseline_score(candidate)
        _baseline_cache[cid] = score

    for d in score.dimensions:
        if d.dimension == override.dimension:
            d.score = override.override_score
            d.explanation = f"[Committee Override] {override.note or 'Manual adjustment'} (original explanation: {d.explanation})"
            break
    else:
        raise HTTPException(status_code=400, detail=f"Unknown dimension: {override.dimension}")

    # Recompute overall
    weights = ScoringWeights()
    score.overall_score = recompute_overall(score, weights)
    if score.overall_score >= 70:
        score.recommendation = "recommend"
    elif score.overall_score >= 50:
        score.recommendation = "consider"
    else:
        score.recommendation = "needs attention"

    # Update cache
    if score.scorer_type == "ai":
        _score_cache[cid] = score
    else:
        _baseline_cache[cid] = score
    return score


@router.post("/reweight", response_model=list[RankedCandidate])
def reweight(weights: ScoringWeights, scorer: str = "baseline"):
    """Re-rank with new weights without re-scoring."""
    candidates = load_candidates()
    cache = _score_cache if scorer == "ai" else _baseline_cache
    if not cache:
        for c in candidates:
            _baseline_cache[c.id] = compute_baseline_score(c, weights)
        cache = _baseline_cache
    return rank_candidates(candidates, cache, weights)
