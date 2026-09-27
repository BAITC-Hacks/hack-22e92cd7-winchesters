"""Attribute-grouped fairness audit (FAIR-07).

Committee and admin only: the response joins self-declared background to
levels, which is exactly what an interviewer or applicant must not browse.

`source=synthetic` (the default until LED-11 stores real levels) audits a
generated cohort and says so in the body; `source=db` audits whatever
`protected_attributes` × `competency_scores` holds, which today is nothing.
The numbers match `python -m backend.scoring.fairness_audit` for the same
source and seeds.
"""

from __future__ import annotations

import copy
import hashlib
import logging
import asyncio
import statistics
from functools import cache
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlmodel import Session

from backend import llm, settings
from backend.db import model_runs
from backend.db.fairness import load_audit_records
from backend.db.candidates import applicant_id_for
from backend.db.engine import get_engine
from backend.db.tables import AuditLogEntry, ModelRunStatus
from backend.models import Candidate, CandidateScore
from backend.routers.candidates import get_candidate_or_404
from backend.routers.candidates import load_candidates
from backend.routers.guards import require_role
from backend.scoring.ai_scorer import SCORING_PROMPT, SYSTEM_PROMPT, compute_ai_score
from backend.scoring.baseline import compute_baseline_score
from backend.scoring import fairness_audit, synthetic_cohort
from backend.evals import cohort_probe
from backend.security import Role

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/fairness",
    tags=["fairness"],
    dependencies=[Depends(require_role(Role.COMMITTEE, Role.ADMIN))],
)


class GroupOut(BaseModel):
    group: str
    n: int
    share_of_pool: float
    levels: dict[str, int]
    high_rate: float
    no_evidence_rate: float
    impact_ratio: float | None
    ci_low: float | None
    ci_high: float | None
    is_reference: bool
    state: Literal["ok", "review_needed", "not_enough_data"]
    review_reason: Literal["below_threshold", "interval_crosses_threshold"] | None


class CellOut(BaseModel):
    competency: str
    pool: int
    reference_group: str | None
    groups: list[GroupOut]


class DimensionOut(BaseModel):
    dimension: str
    undeclared: int
    competencies: list[CellOut]


class MethodOut(BaseModel):
    outcome: str
    reference: str
    interval: str
    bootstrap_seed: int
    n_bootstrap: int
    review_threshold: float
    min_group_n: int
    min_group_share: float


class SyntheticOut(BaseModel):
    cohort_seed: int
    size: int
    planted_effects: list[dict[str, str]]
    notice: str


class AuditOut(BaseModel):
    source: Literal["synthetic", "db"]
    applicants: int
    applicants_with_levels: int
    input_hash: str
    method: MethodOut
    competencies: list[str]
    dimensions: list[DimensionOut]
    synthetic: SyntheticOut | None = None


class ProbeVariant(BaseModel):
    id: str
    marker: str
    changed_markers: list[str]
    score: CandidateScore
    signed_delta: float
    competency_deltas: dict[str, float]
    level_flips: list[str]


class ProbeOut(BaseModel):
    candidate_id: str
    status: Literal["live", "cached_demo", "fallback_demo"]
    baseline: CandidateScore
    variants: list[ProbeVariant]
    signed_delta: float
    noise_sd: float
    tolerance: float
    flips_for_human_review: list[str]
    changed_markers: list[str]
    prompt_id: str
    model_id: str
    notice: str


class CohortProbeOut(BaseModel):
    status: Literal["live", "cached", "fallback"]
    mode: Literal["live", "cached", "fallback"]
    sampled_candidates: int
    markers: list[str]
    competencies: list[str]
    cells: list[dict[str, Any]]
    failed_cells: list[dict[str, Any]]
    passed: bool
    threshold: float
    noise_sd: float
    tolerance: float
    fixture_hash: str
    prompt_id: str
    model_id: str
    production_invariance: dict[str, bool]
    live: dict[str, Any] | None
    cached: dict[str, Any] | None
    fallback: dict[str, Any] | None


PROBE_STAGE = "fairness_probe"
PROBE_REPEAT_COUNT = 5
PROMPT_ID = hashlib.sha256(f"{SYSTEM_PROMPT}\n{SCORING_PROMPT}".encode()).hexdigest()[:16]
PROBE_MARKERS = ["name", "region", "school_type", "language", "speech_style", "name"]


def _candidate_variant(candidate: Candidate, marker: str, index: int) -> Candidate:
    variant = copy.deepcopy(candidate)
    if marker == "name":
        variant.name = "Aruzhan S." if index == 0 else "Ivan P."
    elif marker == "region":
        variant.essay.text = f"Region marker: {'Almaty' if index % 2 else 'Kyzylorda'}.\n{variant.essay.text}"
    elif marker == "school_type":
        variant.application.education.school_type = "public" if index % 2 else "village school"
    elif marker == "language":
        variant.application.languages = ["kk"] if index % 2 else ["ru"]
    elif marker == "speech_style":
        variant.essay.text = variant.essay.text.replace(".", "... um,", 2)
    return variant


def _score_payload(score: CandidateScore) -> dict[str, Any]:
    return score.model_dump(mode="json")


def _record_probe_run(applicant_id: str, score: CandidateScore, *, marker: str) -> None:
    model_runs.record_model_run(
        stage=PROBE_STAGE,
        model=settings.MODEL_JUDGE,
        status=ModelRunStatus.OK.value,
        output={"marker": marker, "score": _score_payload(score), "prompt_id": PROMPT_ID},
        applicant_id=applicant_id,
    )


def _demo_probe(candidate: Candidate) -> tuple[CandidateScore, list[CandidateScore]]:
    baseline = compute_baseline_score(candidate)
    variants = [
        compute_baseline_score(_candidate_variant(candidate, marker, index))
        for index, marker in enumerate(PROBE_MARKERS)
    ]
    return baseline, variants


def _probe_level(score: float) -> int:
    if score >= 66.7:
        return 3
    if score >= 33.3:
        return 2
    return 1


def _probe_result(
    candidate_id: str,
    baseline: CandidateScore,
    scores: list[CandidateScore],
    *,
    status: Literal["live", "cached_demo", "fallback_demo"],
    noise_sd: float,
    reason: str = "",
) -> ProbeOut:
    tolerance = round(2 * noise_sd, 2)
    variants: list[ProbeVariant] = []
    flips: list[str] = []
    for index, score in enumerate(scores):
        dimension_deltas = {
            dimension.dimension: round(dimension.score - base.score, 1)
            for dimension, base in zip(score.dimensions, baseline.dimensions)
        }
        variant_dimensions = {dimension.dimension: dimension.score for dimension in score.dimensions}
        baseline_dimensions = {dimension.dimension: dimension.score for dimension in baseline.dimensions}
        level_flips = [
            name
            for name, delta in dimension_deltas.items()
            if abs(delta) > tolerance
            and _probe_level(variant_dimensions[name]) != _probe_level(baseline_dimensions[name])
        ]
        if level_flips:
            flips.extend(f"{PROBE_MARKERS[index]}: {name}" for name in level_flips)
        variants.append(
            ProbeVariant(
                id=f"variant-{index + 1}",
                marker=PROBE_MARKERS[index],
                changed_markers=[PROBE_MARKERS[index]],
                score=score,
                signed_delta=round(score.overall_score - baseline.overall_score, 1),
                competency_deltas=dimension_deltas,
                level_flips=level_flips,
            )
        )
    signed_delta = round(sum(v.signed_delta for v in variants) / len(variants), 1)
    return ProbeOut(
        candidate_id=candidate_id,
        status=status,
        baseline=baseline,
        variants=variants,
        signed_delta=signed_delta,
        noise_sd=round(noise_sd, 2),
        tolerance=tolerance,
        flips_for_human_review=flips,
        changed_markers=PROBE_MARKERS,
        prompt_id=PROMPT_ID,
        model_id=settings.MODEL_JUDGE if status == "live" else "cached-baseline-demo",
        notice=(
            "Live re-score: six variants and five same-text repeats used the same scorer."
            if status == "live"
            else (
                f"Not a model result ({reason or 'cached demo'}): the AI scorer was not called. Every variant was "
                "scored by the deterministic baseline, so this shows the probe mechanism, not the AI's behaviour. "
                "No score or ranking was changed."
            )
        ),
    )


def _record_probe_audit(actor_id: str, candidate_id: str, result: ProbeOut) -> None:
    with Session(get_engine()) as session:
        session.add(
            AuditLogEntry(
                actor_user_id=actor_id,
                action="fairness_probe_run",
                object_type="candidate",
                object_id=candidate_id,
                after={
                    "status": result.status,
                    "signed_delta": result.signed_delta,
                    "tolerance": result.tolerance,
                    "flips_for_human_review": result.flips_for_human_review,
                    "prompt_id": result.prompt_id,
                    "model_id": result.model_id,
                },
            )
        )
        session.commit()


SYNTHETIC_NOTICE = (
    "Synthetic data: generated profiles, no real applicants. "
    "It demonstrates the method, not evidence about the scorer."
)


@cache
def _synthetic_report() -> dict:
    """Fixed seeds, so the same every time: computed once per process."""
    report = fairness_audit.run_audit(synthetic_cohort.generate(), source="synthetic")
    report["synthetic"] = {
        "cohort_seed": synthetic_cohort.DEFAULT_SEED,
        "size": synthetic_cohort.DEFAULT_SIZE,
        "planted_effects": list(synthetic_cohort.PLANTED_EFFECTS),
        "notice": SYNTHETIC_NOTICE,
    }
    return report


@router.get("/audit", response_model=AuditOut)
def audit(source: Literal["synthetic", "db"] = Query("synthetic")):
    if source == "synthetic":
        return _synthetic_report()
    return fairness_audit.run_audit(load_audit_records(), source="db")


@router.post("/probe/{candidate_id}", response_model=ProbeOut)
async def probe(
    candidate_id: str,
    live: bool = Query(True),
    user: dict[str, Any] = Depends(require_role(Role.COMMITTEE, Role.ADMIN)),
):
    """Run an isolated counterfactual probe; it never writes a score run."""
    candidate = await run_in_threadpool(get_candidate_or_404, candidate_id)
    applicant_id = await run_in_threadpool(applicant_id_for, candidate_id)

    if not live:
        baseline, variants = _demo_probe(candidate)
        result = _probe_result(candidate_id, baseline, variants, status="cached_demo", noise_sd=0.0)
        await run_in_threadpool(_record_probe_audit, user["id"], candidate_id, result)
        return result

    try:
        repeats = await asyncio.gather(*(compute_ai_score(candidate) for _ in range(PROBE_REPEAT_COUNT)))
        baseline = repeats[0]
        noise_sd = statistics.pstdev([score.overall_score for score in repeats])
        variants = await asyncio.gather(
            *(compute_ai_score(_candidate_variant(candidate, marker, index)) for index, marker in enumerate(PROBE_MARKERS))
        )
        for score in repeats:
            await run_in_threadpool(_record_probe_run, applicant_id, score, marker="same_text")
        for marker, score in zip(PROBE_MARKERS, variants):
            await run_in_threadpool(_record_probe_run, applicant_id, score, marker=marker)
        result = _probe_result(candidate_id, baseline, list(variants), status="live", noise_sd=noise_sd)
    except Exception as error:
        logger.warning("Fairness probe fell back for %s: %s", candidate_id, error)
        reason = "no model API key on this server" if isinstance(error, llm.ModelUnavailable) else "the live model call failed"
        baseline, variants = _demo_probe(candidate)
        result = _probe_result(candidate_id, baseline, variants, status="fallback_demo", noise_sd=0.0, reason=reason)

    await run_in_threadpool(_record_probe_audit, user["id"], candidate_id, result)
    return result


@router.get("/cohort-probe", response_model=CohortProbeOut)
async def cohort_probe_report(
    live: bool = Query(False),
    _user: dict[str, Any] = Depends(require_role(Role.COMMITTEE, Role.ADMIN)),
):
    """Run FAIR-11 over a deterministic 36-candidate sample without scoring writes."""
    candidates = await run_in_threadpool(load_candidates)
    return await cohort_probe.run(candidates, live=live)


@router.post("/scorer-versions/{version}/publish")
async def publish_scorer_version(
    version: str,
    live: bool = Query(True),
    user: dict[str, Any] = Depends(require_role(Role.COMMITTEE, Role.ADMIN)),
):
    """Publish only after the current cohort probe passes.

    This is a governance record, not a switch in the production scorer.
    """
    candidates = await run_in_threadpool(load_candidates)
    report = await cohort_probe.run(candidates, live=live)
    if report["status"] == "fallback":
        raise HTTPException(status_code=503, detail={"message": "Live cohort probe unavailable; scorer version was not published.", "probe": report})
    if not report["passed"]:
        raise HTTPException(status_code=409, detail={"message": "Cohort probe failed; scorer version was not published.", "probe": report})

    def record_publish() -> None:
        with Session(get_engine()) as session:
            session.add(AuditLogEntry(
                actor_user_id=user["id"],
                action="scorer_version_published",
                object_type="scorer_version",
                object_id=version,
                after={"version": version, "probe": report},
            ))
            session.commit()

    await run_in_threadpool(record_publish)
    return {"version": version, "status": "published", "probe": report}
