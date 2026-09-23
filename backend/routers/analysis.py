"""AI detection and deep analysis endpoints.

Committee and admin only (FND-05): the whole router carries the guard.

Nothing is cached in memory. The ai-detection view is a deterministic shim
since LED-02 (no model call, no verdict) and is computed per request; it is not
stored because it is being retired with LED-05. Video analyses that a model
actually produced are stored in `model_runs` (stage "video_analysis").
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool

from backend import settings
from backend.db import model_runs
from backend.db.candidates import applicant_id_for
from backend.db.tables import ModelRunStatus
from backend.models import AIDetectionResult, VideoAnalysisResult
from backend.routers.candidates import get_candidate_or_404, load_candidates
from backend.routers.guards import require_role
from backend.scoring.ai_detector import detect_ai_content
from backend.scoring.video_analyzer import analyze_video, whisper_available
from backend.security import Role

VIDEO_STAGE = "video_analysis"

# What `analyze_video` returns in place of raising when the model call fails.
# Matching on text is fragile; the fix is for it to raise (see the PR notes).
_VIDEO_UNAVAILABLE_PREFIX = "Analysis unavailable"

router = APIRouter(
    prefix="/api/analysis",
    tags=["analysis"],
    dependencies=[Depends(require_role(Role.COMMITTEE, Role.ADMIN))],
)


@router.post("/ai-detection/{candidate_id}", response_model=AIDetectionResult)
async def detect_ai(candidate_id: str):
    """Analyze a candidate's essay for AI-generated content."""
    candidate = await run_in_threadpool(get_candidate_or_404, candidate_id)
    try:
        return await detect_ai_content(candidate)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI detection failed: {str(e)}")


@router.get("/ai-detection/results", response_model=dict[str, AIDetectionResult])
async def get_all_detection_results():
    """The ai-detection view for every candidate, computed now."""
    candidates = await run_in_threadpool(load_candidates)
    return {c.id: await detect_ai_content(c) for c in candidates}


def _video_model(result: VideoAnalysisResult) -> str:
    # Mirrors the choice in backend.scoring.video_analyzer.analyze_video.
    if result.language_detected != "english":
        return settings.MODEL_FOR_LOW_RESOURCE
    return settings.MODEL_EXTRACT


def _record_video(applicant_id: str, result: VideoAnalysisResult) -> None:
    """Store a real analysis as ok and a swallowed failure as failed.

    An analysis of the mock transcript is not stored: it says nothing about
    this applicant.
    """
    if result.is_mock:
        return
    if result.summary.startswith(_VIDEO_UNAVAILABLE_PREFIX):
        model_runs.record_model_run(
            stage=VIDEO_STAGE,
            model=_video_model(result),
            status=ModelRunStatus.FAILED.value,
            error=result.summary,
            applicant_id=applicant_id,
        )
        return
    model_runs.record_model_run(
        stage=VIDEO_STAGE,
        model=_video_model(result),
        status=ModelRunStatus.OK.value,
        output=result.model_dump(mode="json"),
        applicant_id=applicant_id,
    )


@router.post("/video-analysis/{candidate_id}", response_model=VideoAnalysisResult)
async def analyze_video_endpoint(candidate_id: str):
    """Analyze a candidate's video presentation transcript.

    Compares video voice with essay voice for authenticity,
    extracts motivation signals and growth indicators.
    Uses Whisper API if OPENAI_API_KEY is set, otherwise mock/pasted transcript.
    Returns the stored analysis if there is one; runs the model otherwise.
    """
    candidate = await run_in_threadpool(get_candidate_or_404, candidate_id)
    applicant_id = await run_in_threadpool(applicant_id_for, candidate.id)
    stored = await run_in_threadpool(model_runs.latest_ok_output, applicant_id, VIDEO_STAGE)
    if stored is not None:
        return VideoAnalysisResult.model_validate(stored)

    try:
        result = await analyze_video(candidate)
    except Exception as e:
        # analyze_video handles model errors itself, so this failed before a
        # model was chosen; the record says so rather than guessing one.
        await run_in_threadpool(
            model_runs.record_model_run,
            stage=VIDEO_STAGE,
            model="unknown",
            status=ModelRunStatus.FAILED.value,
            error=f"{type(e).__name__}: {e}",
            applicant_id=applicant_id,
        )
        raise HTTPException(status_code=500, detail=f"Video analysis failed: {str(e)}")
    await run_in_threadpool(_record_video, applicant_id, result)
    return result


@router.get("/video-analysis/status")
def video_analysis_status():
    """Check if real Whisper transcription is available."""
    return {
        "whisper_available": whisper_available(),
        "mode": "whisper" if whisper_available() else "mock/text",
        "note": "Set OPENAI_API_KEY in .env to enable real video transcription",
    }
