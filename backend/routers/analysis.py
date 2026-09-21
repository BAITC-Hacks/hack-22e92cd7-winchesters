"""AI detection and deep analysis endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from backend.models import AIDetectionResult, VideoAnalysisResult
from backend.routers.candidates import get_candidate_or_404
from backend.scoring.ai_detector import detect_ai_content
from backend.scoring.video_analyzer import analyze_video, whisper_available

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

_detection_cache: dict[str, AIDetectionResult] = {}
_video_cache: dict[str, VideoAnalysisResult] = {}


@router.post("/ai-detection/{candidate_id}", response_model=AIDetectionResult)
async def detect_ai(candidate_id: str):
    """Analyze a candidate's essay for AI-generated content."""
    if candidate_id in _detection_cache:
        return _detection_cache[candidate_id]

    candidate = await run_in_threadpool(get_candidate_or_404, candidate_id)
    try:
        result = await detect_ai_content(candidate)
        _detection_cache[candidate_id] = result
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI detection failed: {str(e)}")


@router.get("/ai-detection/results", response_model=dict[str, AIDetectionResult])
def get_all_detection_results():
    """Get all cached AI detection results."""
    return _detection_cache


@router.post("/video-analysis/{candidate_id}", response_model=VideoAnalysisResult)
async def analyze_video_endpoint(candidate_id: str):
    """Analyze a candidate's video presentation transcript.

    Compares video voice with essay voice for authenticity,
    extracts motivation signals and growth indicators.
    Uses Whisper API if OPENAI_API_KEY is set, otherwise mock/pasted transcript.
    """
    if candidate_id in _video_cache:
        return _video_cache[candidate_id]

    candidate = await run_in_threadpool(get_candidate_or_404, candidate_id)
    try:
        result = await analyze_video(candidate)
        _video_cache[candidate_id] = result
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video analysis failed: {str(e)}")


@router.get("/video-analysis/status")
def video_analysis_status():
    """Check if real Whisper transcription is available."""
    return {
        "whisper_available": whisper_available(),
        "mode": "whisper" if whisper_available() else "mock/text",
        "note": "Set OPENAI_API_KEY in .env to enable real video transcription",
    }
