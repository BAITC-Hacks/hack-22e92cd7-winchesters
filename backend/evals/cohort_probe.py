"""FAIR-11 cohort robustness probes, isolated from production scoring."""

from __future__ import annotations

import asyncio
import hashlib
import statistics
from typing import Any

from backend import settings
from backend.models import Candidate, CandidateScore
from backend.scoring.ai_scorer import compute_ai_score
from backend.scoring.baseline import compute_baseline_score

COHORT_SEED = 611
SAMPLE_SIZE = 36
MIN_ROBUSTNESS_RATE = 0.95
PROBE_MARKERS = ("name", "region", "school_type", "language", "speech_style")


def _fairness_helpers():
    # Import after router initialization to reuse FAIR-06 semantics without a
    # module-level circular import.
    from backend.routers.fairness import PROMPT_ID, _candidate_variant, _probe_level

    return PROMPT_ID, _candidate_variant, _probe_level


def _sample(candidates: list[Candidate]) -> list[Candidate]:
    if not candidates:
        return []
    return [candidates[index % len(candidates)] for index in range(SAMPLE_SIZE)]


def _fixture_hash(candidates: list[Candidate]) -> str:
    body = "|".join(candidate.id for candidate in candidates)
    return hashlib.sha256(body.encode()).hexdigest()


def _rows(cases: list[Candidate], baselines: list[CandidateScore], variants: list[list[CandidateScore]], tolerance: float) -> list[dict[str, Any]]:
    _, _, probe_level = _fairness_helpers()
    rows: list[dict[str, Any]] = []
    for candidate, baseline, candidate_variants in zip(cases, baselines, variants):
        baseline_by_dimension = {item.dimension: item.score for item in baseline.dimensions}
        for marker, variant in zip(PROBE_MARKERS, candidate_variants):
            for dimension in variant.dimensions:
                base = baseline_by_dimension.get(dimension.dimension, baseline.overall_score)
                robust = not (abs(dimension.score - base) > tolerance and probe_level(dimension.score) != probe_level(base))
                rows.append({"candidate_id": candidate.id, "marker": marker, "competency": dimension.dimension, "robust": robust, "delta": round(dimension.score - base, 1)})
    return rows


def _report(cases: list[Candidate], baselines: list[CandidateScore], variants: list[list[CandidateScore]], *, mode: str, noise_sd: float, fixture_hash: str) -> dict[str, Any]:
    prompt_id, _, _ = _fairness_helpers()
    tolerance = round(2 * noise_sd, 2)
    rows = _rows(cases, baselines, variants, tolerance)
    cells = []
    for marker in PROBE_MARKERS:
        for competency in sorted({row["competency"] for row in rows}):
            cell = [row for row in rows if row["marker"] == marker and row["competency"] == competency]
            robust = sum(row["robust"] for row in cell)
            cells.append({"marker": marker, "competency": competency, "sampled_candidates": len(cell), "robust_count": robust, "robustness_rate": round(robust / len(cell), 3) if cell else 0.0, "passed": bool(cell) and robust / len(cell) >= MIN_ROBUSTNESS_RATE})
    failed = [cell for cell in cells if not cell["passed"]]
    return {
        "mode": mode,
        "sampled_candidates": len(cases),
        "markers": list(PROBE_MARKERS),
        "competencies": sorted({row["competency"] for row in rows}),
        "cells": cells,
        "failed_cells": failed,
        "passed": not failed and bool(cells),
        "threshold": MIN_ROBUSTNESS_RATE,
        "noise_sd": round(noise_sd, 2),
        "tolerance": tolerance,
        "fixture_hash": fixture_hash,
        "prompt_id": prompt_id,
        "model_id": settings.MODEL_JUDGE if mode == "live" else "cached-baseline-demo",
        "production_invariance": {"score_path_changed": False, "ranking_changed": False, "recommendation_changed": False},
    }


def cached_report(candidates: list[Candidate]) -> dict[str, Any]:
    _, candidate_variant, _ = _fairness_helpers()
    cases = _sample(candidates)
    baselines = [compute_baseline_score(candidate) for candidate in cases]
    variants = [[compute_baseline_score(candidate_variant(candidate, marker, index)) for index, marker in enumerate(PROBE_MARKERS)] for candidate in cases]
    return _report(cases, baselines, variants, mode="cached", noise_sd=0.0, fixture_hash=_fixture_hash(cases))


async def live_report(candidates: list[Candidate]) -> dict[str, Any]:
    _, candidate_variant, _ = _fairness_helpers()
    cases = _sample(candidates)
    baselines = list(await asyncio.gather(*(compute_ai_score(candidate) for candidate in cases)))
    repeats = await asyncio.gather(*(compute_ai_score(cases[0]) for _ in range(5)))
    variants = [list(await asyncio.gather(*(compute_ai_score(candidate_variant(candidate, marker, index)) for index, marker in enumerate(PROBE_MARKERS)))) for candidate in cases]
    return _report(cases, baselines, variants, mode="live", noise_sd=statistics.pstdev([score.overall_score for score in repeats]), fixture_hash=_fixture_hash(cases))


async def run(candidates: list[Candidate], live: bool) -> dict[str, Any]:
    cached = cached_report(candidates)
    if not live:
        return {"status": "cached", "live": None, "cached": cached, "fallback": None, **cached}
    try:
        live_result = await live_report(candidates)
        return {"status": "live", "live": live_result, "cached": None, "fallback": None, **live_result}
    except Exception:
        return {"status": "fallback", "live": None, "cached": cached, "fallback": cached, **cached, "mode": "fallback"}