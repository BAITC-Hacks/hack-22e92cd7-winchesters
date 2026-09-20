"""Video presentation analysis — transcript extraction + Claude evaluation.

Supports two modes:
1. Real mode: OpenAI Whisper API transcribes audio → Claude analyzes
2. Mock mode: Uses candidate's pasted transcript or generates mock data
3. Text mode: Student pastes transcript directly → Claude analyzes

To enable real Whisper: add OPENAI_API_KEY to .env
"""

from __future__ import annotations

import json
import os

from backend.ai_client import MODEL, get_client, text_of
from backend.models import Candidate, VideoAnalysisResult
from backend.privacy import anonymize_candidate
from backend.scoring.ai_detector import detect_language

_openai_client = None


def _get_openai():
    """Returns OpenAI client if key is available, else None."""
    global _openai_client
    if _openai_client is not None:
        return _openai_client
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return None
    try:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=key)
        return _openai_client
    except ImportError:
        return None


def whisper_available() -> bool:
    """Check if Whisper API is available."""
    return _get_openai() is not None


async def transcribe_audio(file_path: str) -> str:
    """Transcribe audio/video file using OpenAI Whisper API.

    Returns the transcript text. Only works if OPENAI_API_KEY is set.
    """
    client = _get_openai()
    if client is None:
        raise RuntimeError("OpenAI API key not configured. Set OPENAI_API_KEY in .env")

    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text",
        )
    return transcription


# ── Mock transcript for demo ───────────────────────────────────────

MOCK_TRANSCRIPT = """
Hello, my name is... well, I'm applying to inVision U because I genuinely believe
this is where I can grow the most. I come from a small town, and honestly, I didn't
think university was something people like me could reach.

But last year something changed. I started a project in my community — it was small,
just helping organize transport for families who couldn't get to the city. And I realized
that I actually enjoy solving problems that affect real people. Not theoretical problems
from textbooks, but actual, messy, complicated real-life problems.

My biggest challenge was convincing adults to trust a teenager with their money.
I had to create a budget, present it at a village meeting, and defend my numbers
in front of people twice my age. It was terrifying, but when the project actually
worked, it changed how I see myself.

I want to study at inVision U because I want to learn how to scale what I've started.
I don't just want to help one village — I want to understand how systems work so I
can help many communities. I know my grades aren't perfect, but I believe my experience
and motivation show that I'm ready to work harder than anyone.

My dream is to build things that make life easier for people who don't have many
advantages. That's what drives me. Thank you.
""".strip()


# ── Claude analysis prompt ─────────────────────────────────────────

VIDEO_ANALYSIS_PROMPT = """You are analyzing a university admissions video presentation transcript.
The candidate submitted both a written essay and a video presentation.

ESSAY TEXT:
{essay_text}

VIDEO TRANSCRIPT:
{video_transcript}

Analyze the video transcript and compare it with the essay. Return your analysis as JSON:

{{
  "authenticity_match": <0-100, how well the video voice matches the essay voice.
    High = consistent personality and vocabulary across both.
    Low = essay sounds AI-generated but video sounds natural, or vice versa>,
  "motivation_score": <0-100, how genuine and driven the candidate appears based on video>,
  "key_themes": ["<theme 1>", "<theme 2>", ...],
  "growth_signals": ["<specific growth signal from video>", ...],
  "concerns": ["<concern if any>", ...],
  "summary": "<2-3 sentence assessment of the candidate based on their video>"
}}

Key things to evaluate:
- Does the speaking style match the writing style? (vocabulary level, sentence complexity)
- Does the candidate mention specific personal experiences, or speak in generalities?
- Are there signs of genuine motivation, or does it sound rehearsed/generic?
- Does the video reveal anything the essay doesn't?

Return ONLY valid JSON, no markdown fences."""


async def analyze_video(candidate: Candidate) -> VideoAnalysisResult:
    """Analyze a candidate's video presentation.

    Uses real Whisper transcription if OPENAI_API_KEY is set,
    otherwise uses the candidate's pasted transcript or mock data.
    """
    safe = anonymize_candidate(candidate)

    # Determine transcript source
    transcript = ""
    is_mock = False

    if candidate.video_transcript and candidate.video_transcript.strip():
        # Student pasted their own transcript
        transcript = candidate.video_transcript.strip()
    elif whisper_available() and candidate.video_link:
        # TODO: Download video from link, extract audio, transcribe
        # For now, this path requires a local file upload
        transcript = MOCK_TRANSCRIPT
        is_mock = True
    else:
        # No transcript available — use mock for demo
        transcript = MOCK_TRANSCRIPT
        is_mock = True

    # Detect language
    lang = detect_language(transcript)

    # Run Claude analysis
    client = get_client()
    prompt = VIDEO_ANALYSIS_PROMPT.format(
        essay_text=safe.essay.text,
        video_transcript=transcript,
    )

    try:
        # max_tokens covers adaptive thinking + the JSON answer on this model
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = text_of(response).strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]

        data = json.loads(raw.strip())

        return VideoAnalysisResult(
            transcript=transcript,
            language_detected=lang,
            authenticity_match=data.get("authenticity_match", 0),
            motivation_score=data.get("motivation_score", 0),
            key_themes=data.get("key_themes", []),
            growth_signals=data.get("growth_signals", []),
            concerns=data.get("concerns", []),
            summary=data.get("summary", ""),
            is_mock=is_mock,
        )
    except Exception as e:
        return VideoAnalysisResult(
            transcript=transcript,
            language_detected=lang,
            summary=f"Analysis failed: {str(e)}",
            is_mock=is_mock,
        )
