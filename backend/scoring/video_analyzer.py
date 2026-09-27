"""Video presentation analysis: compare a transcript with the essay.

The written presentation is the canonical presentation input (INP-01); a video
transcript is auxiliary. This module only ever analyses a transcript that
exists. With no transcript it returns `status="no_transcript"`, carries no
numbers and calls no model: an applicant must never be scored on text that is
not theirs. There is no mock transcript and no fallback to one.

Speech recognition is not run here. If it is ever switched on it is ElevenLabs
Scribe v2 only, pinned in `backend.settings`; Whisper is barred for Kazakh.
"""

from __future__ import annotations

import logging

from backend import llm, settings
from backend.models import Candidate, VideoAnalysisResult
from backend.privacy import anonymize_candidate
from backend.scoring.ai_detector import detect_language

logger = logging.getLogger(__name__)

NO_TRANSCRIPT_SUMMARY = "No transcript — nothing was scored."
UNAVAILABLE_SUMMARY = "Analysis unavailable — the transcript was not assessed."


# ── Speech recognition (not run in this build) ─────────────────────


def asr_status() -> dict:
    """Whether a transcript could be produced from a video, and by what.

    Needs both the explicit flag and a key. Without them the answer is a plain
    "unavailable", and applicants' videos are simply not transcribed.
    """
    available = settings.ASR_ENABLED and bool(settings.ELEVENLABS_API_KEY)
    if available:
        reason = ""
    elif not settings.ASR_ENABLED:
        reason = "ASR unavailable: switched off (set ASR_ENABLED=1 and ELEVENLABS_API_KEY to enable)."
    else:
        reason = "ASR unavailable: ELEVENLABS_API_KEY is not set."
    return {
        "available": available,
        "provider": settings.ASR_PROVIDER,
        "model": settings.ASR_MODEL,
        "reason": reason,
    }


# ── Claude analysis prompt ─────────────────────────────────────────

VIDEO_ANALYSIS_PROMPT = """You are analyzing a university admissions video presentation transcript.
The candidate submitted both a written essay and a video presentation.

{essay_document}

{video_document}

Compare the video transcript with the essay.

Key things to evaluate:
- Does the speaking style match the writing style? (vocabulary level, sentence complexity)
- Does the candidate mention specific personal experiences, or speak in generalities?
- Are there signs of genuine motivation, or does it sound rehearsed/generic?
- Does the video reveal anything the essay doesn't?

Score authenticity_match from 0 to 100: high means a consistent personality and
vocabulary across both sources; low means the two voices do not look like the
same person.

Score motivation_score from 0 to 100 based on what the candidate says about why
they want this, not on how fluent or polished the delivery is.

A transcript of speech is disfluent by nature, and a transcript of Kazakh speech
carries a high error rate from the transcription system itself. Never read
hesitation, repetition, grammatical slips or garbled words as a signal about the
candidate. Raise a concern only for something the candidate actually said."""

VIDEO_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "authenticity_match",
        "motivation_score",
        "key_themes",
        "growth_signals",
        "concerns",
        "summary",
    ],
    "properties": {
        "authenticity_match": {"type": "number"},
        "motivation_score": {"type": "number"},
        "key_themes": {"type": "array", "items": {"type": "string"}},
        "growth_signals": {"type": "array", "items": {"type": "string"}},
        "concerns": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
}


def model_for(language: str) -> str:
    """Kazakh and mixed-language transcripts go to the strongest model."""
    return settings.MODEL_FOR_LOW_RESOURCE if language != "english" else settings.MODEL_EXTRACT


async def analyze_video(candidate: Candidate) -> VideoAnalysisResult:
    """Analyse the applicant's own transcript, or say plainly there is none."""
    transcript = candidate.video_transcript.strip()
    if not transcript:
        return VideoAnalysisResult(status="no_transcript", summary=NO_TRANSCRIPT_SUMMARY)

    lang = detect_language(transcript)
    if not llm.is_configured():
        # No key on this server: say so before trying, and score nothing.
        return VideoAnalysisResult(
            status="unavailable", transcript=transcript, language_detected=lang, summary=UNAVAILABLE_SUMMARY
        )

    safe = anonymize_candidate(candidate)
    prompt = VIDEO_ANALYSIS_PROMPT.format(
        essay_document=llm.wrap_document(safe.essay.text, "essay", safe.id),
        video_document=llm.wrap_document(safe.video_transcript.strip(), "video_transcript", safe.id),
    )
    try:
        payload = await llm.complete_json(prompt=prompt, schema=VIDEO_SCHEMA, model=model_for(lang))
    except Exception:
        # Log the cause here; the caller gets a result that is plainly marked as
        # unavailable, with no number that could rank like a real score.
        logger.exception("video analysis failed for %s", candidate.id)
        return VideoAnalysisResult(
            status="unavailable", transcript=transcript, language_detected=lang, summary=UNAVAILABLE_SUMMARY
        )

    return VideoAnalysisResult(
        status="analyzed",
        transcript=transcript,
        language_detected=lang,
        authenticity_match=max(0.0, min(float(payload["authenticity_match"]), 100.0)),
        motivation_score=max(0.0, min(float(payload["motivation_score"]), 100.0)),
        key_themes=payload["key_themes"],
        growth_signals=payload["growth_signals"],
        concerns=payload["concerns"],
        summary=payload["summary"],
    )
