"""AI detection and deep analysis endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.models import AIDetectionResult
from backend.routers.candidates import _get_candidate
from backend.scoring.ai_detector import detect_ai_content

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

_detection_cache: dict[str, AIDetectionResult] = {}


@router.post("/ai-detection/{candidate_id}", response_model=AIDetectionResult)
async def detect_ai(candidate_id: str):
    """Analyze a candidate's essay for AI-generated content."""
    if candidate_id in _detection_cache:
        return _detection_cache[candidate_id]

    candidate = _get_candidate(candidate_id)
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
