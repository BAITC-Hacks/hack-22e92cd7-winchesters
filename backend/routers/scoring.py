"""Scoring and ranking endpoints.

Committee and admin only (FND-05): the whole router carries the guard.

AI scores live in `model_runs` (stage "score_ai"), one row per attempt; the
current score is the latest ok run. A failed attempt is stored as failed and
leaves the applicant out of the AI ranking rather than ranking them with a
zero. Baseline scores are deterministic and cheap, so they are computed on
every request and never stored.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool

from backend import settings
from backend.db import model_runs
from backend.db.candidates import applicant_id_for, applicant_ids
from backend.db.tables import ModelRunStatus
from backend.models import Candidate, CandidateScore, RankedCandidate, ScoringWeights
from backend.routers.candidates import get_candidate_or_404, load_candidates
from backend.routers.guards import require_role
from backend.scoring.aggregator import compare_scores, rank_candidates
from backend.scoring.ai_scorer import compute_ai_score
from backend.scoring.baseline import compute_baseline_score
from backend.security import Role

logger = logging.getLogger(__name__)

AI_SCORE_STAGE = "score_ai"

router = APIRouter(
    prefix="/api/scoring",
    tags=["scoring"],
    dependencies=[Depends(require_role(Role.COMMITTEE, Role.ADMIN))],
)


def _record_ai_score(applicant_id: str, result: CandidateScore | BaseException) -> None:
    if isinstance(result, BaseException):
        model_runs.record_model_run(
            stage=AI_SCORE_STAGE,
            model=settings.MODEL_JUDGE,
            status=ModelRunStatus.FAILED.value,
            error=f"{type(result).__name__}: {result}",
            applicant_id=applicant_id,
        )
    else:
        model_runs.record_model_run(
            stage=AI_SCORE_STAGE,
            model=settings.MODEL_JUDGE,
            status=ModelRunStatus.OK.value,
            output=result.model_dump(mode="json"),
            applicant_id=applicant_id,
        )


def _stored_ai_scores() -> dict[str, CandidateScore]:
    """Candidate id -> latest ok AI score. Candidates without one are absent."""
    uuid_of = applicant_ids()
    outputs = model_runs.latest_ok_outputs(AI_SCORE_STAGE)
    return {
        ref: CandidateScore.model_validate(outputs[applicant_id])
        for ref, applicant_id in uuid_of.items()
        if applicant_id in outputs
    }


def _ranked(weights: ScoringWeights | None, scorer: str) -> list[RankedCandidate]:
    candidates = load_candidates()
    if scorer == "ai":
        scores = _stored_ai_scores()
        # Only applicants with an ok run are ranked. Ranking the rest with a
        # zero would put "not scored yet" and "the call failed" at the bottom,
        # where they look exactly like weak applications.
        candidates = [c for c in candidates if c.id in scores]
    else:
        scores = {c.id: compute_baseline_score(c, weights) for c in candidates}
    return rank_candidates(candidates, scores, weights)


# `/all` routes come before `/{candidate_id}`: FastAPI matches in declaration
# order, and `/{candidate_id}` would otherwise take "all" as an id.


@router.post("/baseline/all", response_model=list[CandidateScore])
def score_all_baseline(weights: ScoringWeights | None = None):
    """Compute baseline scores for all candidates."""
    return [compute_baseline_score(c, weights) for c in load_candidates()]


@router.post("/baseline/{candidate_id}", response_model=CandidateScore)
def score_baseline(candidate_id: str, weights: ScoringWeights | None = None):
    """Compute baseline (rule-based) score for a candidate."""
    return compute_baseline_score(get_candidate_or_404(candidate_id), weights)


@router.post("/ai/all", response_model=list[CandidateScore])
async def score_all_ai(weights: ScoringWeights | None = None):
    """Compute AI scores for all candidates.

    Candidates are scored concurrently; the shared semaphore in `backend.llm`
    caps how many calls are open at once. Every attempt is stored. A candidate
    whose run fails is stored as failed and left out of the result rather than
    returned with a zero: a zero sorts to the bottom of the ranking, so an API
    timeout used to look exactly like a weak application.
    """
    candidates: list[Candidate] = await run_in_threadpool(load_candidates)
    uuid_of = await run_in_threadpool(applicant_ids)
    results = await asyncio.gather(
        *(compute_ai_score(c, weights) for c in candidates),
        return_exceptions=True,
    )

    scores = []
    for candidate, result in zip(candidates, results):
        await run_in_threadpool(_record_ai_score, uuid_of[candidate.id], result)
        if isinstance(result, BaseException):
            logger.error("AI scoring failed for %s: %s", candidate.id, result)
            continue
        scores.append(result)
    return scores


@router.post("/ai/{candidate_id}", response_model=CandidateScore)
async def score_ai(candidate_id: str, weights: ScoringWeights | None = None):
    """Compute AI-powered score for a candidate (uses Claude API)."""
    candidate = await run_in_threadpool(get_candidate_or_404, candidate_id)
    applicant_id = await run_in_threadpool(applicant_id_for, candidate.id)
    try:
        score = await compute_ai_score(candidate, weights)
    except Exception as e:
        await run_in_threadpool(_record_ai_score, applicant_id, e)
        raise HTTPException(status_code=500, detail=f"AI scoring failed: {str(e)}")
    await run_in_threadpool(_record_ai_score, applicant_id, score)
    return score


@router.post("/rank", response_model=list[RankedCandidate])
def rank_all(weights: ScoringWeights | None = None, scorer: str = "baseline"):
    """Rank candidates. scorer='baseline' ranks everyone; scorer='ai' ranks
    only candidates with a stored ok AI score."""
    return _ranked(weights, scorer)


@router.get("/compare/{candidate_id}")
def compare(candidate_id: str):
    """Compare baseline vs AI scores for a candidate."""
    candidate = get_candidate_or_404(candidate_id)
    stored = model_runs.latest_ok_output(applicant_id_for(candidate.id), AI_SCORE_STAGE)
    if stored is None:
        raise HTTPException(
            status_code=404,
            detail="AI score not yet computed. Run /api/scoring/ai/{id} first.",
        )
    return compare_scores(compute_baseline_score(candidate), CandidateScore.model_validate(stored))


@router.post("/override", status_code=410)
def override_score():
    """Retired until the override ledger (COM-01) lands.

    This used to rewrite a cached score in place, with no record of who changed
    it or what it was before. Stored model runs are never rewritten, and a
    change that is not recorded is not an override, so for now there is none.
    The body is not read: whatever is sent, the answer is the same.
    """
    raise HTTPException(
        status_code=410,
        detail="Score overrides are disabled until the committee override ledger (COM-01) is in place.",
    )


@router.post("/reweight", response_model=list[RankedCandidate])
def reweight(weights: ScoringWeights, scorer: str = "baseline"):
    """Re-rank with new weights without re-scoring."""
    return _ranked(weights, scorer)
