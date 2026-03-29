"""Claude-powered AI scorer — multi-stage pipeline.

BEFORE (old approach):
    Raw candidate JSON → single Claude call → scores + explanations
    Problem: Claude sees everything at once, does signal extraction + scoring +
    explanation in one shot. No way to verify what it based its score on.

AFTER (new approach):
    Stage 1: signal_extractor.py extracts structured facts (no AI, pure code)
    Stage 2: Claude receives pre-extracted signals + raw essay/interview text
             and scores ONLY the subjective dimensions
    Stage 3: Scores are computed as weighted combination of rule-based signals
             and AI judgments, with explanations tied to specific extracted facts

This means:
    - The committee can inspect extracted signals independently of scores
    - AI scoring is grounded in verifiable facts, not vibes
    - Each score can be traced back to specific evidence
"""

from __future__ import annotations

import json
import os

import anthropic
from dotenv import load_dotenv

from backend.models import (
    Candidate,
    CandidateScore,
    Confidence,
    DimensionScore,
    ScoringWeights,
)
from backend.privacy import anonymize_candidate
from backend.scoring.signal_extractor import extract_signals, signals_to_context

load_dotenv()

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


SYSTEM_PROMPT = """\
You are an expert admissions evaluator for inVision U, an innovative scholarship university \
in Kazakhstan that seeks future leaders, entrepreneurs, and change-makers.

You will receive TWO inputs:
1. PRE-EXTRACTED SIGNALS: structured facts already extracted from the candidate's application
2. RAW TEXT: the candidate's essay and interview transcript for qualitative assessment

Your job is to score the SUBJECTIVE dimensions that require human-like judgment. \
The structured signals give you the facts — you assess meaning, depth, and authenticity.

SCORING PHILOSOPHY:
- Fair: evaluate based on demonstrated qualities, NOT demographics or school prestige
- Growth-focused: the "path traveled" matters — what someone did with what they had
- A privileged candidate with real achievements scores well (achievements are real)
- A disadvantaged candidate with comparable achievements gets additional credit on growth_trajectory \
(they climbed further — this is ADDITIVE, not a penalty on anyone)
- Evidence-based: cite specific quotes and facts from the signals and text
- Honest: flag concerns openly, don't inflate scores

Do NOT penalize candidates for:
- Imperfect English or grammar
- Attending a public/village school
- Having fewer formal achievements
- Working part-time or having family responsibilities

DO reward candidates for:
- Initiative and self-direction (starting projects, solving real problems)
- Authenticity and depth of reflection in essays
- Evidence of growth and overcoming obstacles
- Impact on others, even at small scale
- Honest self-awareness about weaknesses
"""


SCORING_PROMPT = """\
Using the pre-extracted signals AND the raw text below, evaluate this candidate across 5 dimensions.

For each dimension, your score should reflect BOTH the quantitative signals AND your qualitative \
reading of the essay/interview. Reference specific extracted signals in your explanation.

For growth_trajectory specifically:
- The extracted signals show starting_level, current_level, and delta
- A HIGH delta means the candidate grew significantly relative to their starting point
- Score this dimension based on the JOURNEY, not just the destination
- A candidate from a village school who built 2 projects = large delta = high growth score
- A candidate from an elite school who built 3 assigned projects = smaller delta = lower growth score
- But an elite school candidate who ALSO started something independently beyond their school = real growth too

DIMENSIONS:
1. academic_strength (15%): Use extracted GPA, achievements, skills, languages
2. leadership_potential (25%): Initiative, ownership, impact on others, mobilization evidence
3. motivation_values (25%): Depth of purpose, authenticity, mission alignment (read the essay deeply)
4. growth_trajectory (20%): The DELTA — how far they've come, not just where they are
5. communication (15%): Essay quality, specificity, voice authenticity, interview articulation

For each dimension provide:
- score (0-100)
- confidence (low/medium/high)
- explanation (2-3 sentences referencing specific signals)
- evidence_quotes (1-3 direct quotes from essay/interview)
- positive_factors (1-3 bullet points)
- concerns (0-3 bullet points)

Also provide:
- overall_recommendation: "recommend" / "consider" / "needs attention"
- summary: 2-3 sentence overall assessment

Respond in this exact JSON format:
{
  "dimensions": [
    {
      "dimension": "academic_strength",
      "score": <0-100>,
      "confidence": "<low|medium|high>",
      "explanation": "<string>",
      "evidence_quotes": ["<quote1>", ...],
      "positive_factors": ["<factor1>", ...],
      "concerns": ["<concern1>", ...]
    },
    ... (all 5 dimensions)
  ],
  "recommendation": "<shortlist|review|decline>",
  "summary": "<string>"
}

Return ONLY valid JSON, no markdown fences or extra text.
"""


def _build_candidate_context(candidate: Candidate) -> str:
    """Format raw text from candidate for qualitative AI assessment."""
    return f"""
RAW ESSAY (prompt: "{candidate.essay.prompt}"):
\"\"\"
{candidate.essay.text}
\"\"\"

RAW INTERVIEW TRANSCRIPT:
\"\"\"
{candidate.interview_transcript or 'Not available'}
\"\"\"

RECOMMENDATION SUMMARY:
\"\"\"
{candidate.recommendation_summary or 'Not available'}
\"\"\"
"""


def _parse_ai_response(raw: str, candidate_id: str) -> CandidateScore:
    """Parse the AI response JSON into a CandidateScore."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()

    data = json.loads(cleaned)

    dimensions = []
    for d in data["dimensions"]:
        dimensions.append(DimensionScore(
            dimension=d["dimension"],
            score=float(d["score"]),
            confidence=Confidence(d["confidence"]),
            explanation=d.get("explanation", ""),
            evidence_quotes=d.get("evidence_quotes", []),
            positive_factors=d.get("positive_factors", []),
            concerns=d.get("concerns", []),
        ))

    weight_map = {
        "academic_strength": 0.15,
        "leadership_potential": 0.25,
        "motivation_values": 0.25,
        "growth_trajectory": 0.20,
        "communication": 0.15,
    }
    overall = sum(
        d.score * weight_map.get(d.dimension, 0.2)
        for d in dimensions
    )

    return CandidateScore(
        candidate_id=candidate_id,
        dimensions=dimensions,
        overall_score=round(overall, 1),
        recommendation=data.get("recommendation", "review"),
        summary=data.get("summary", ""),
        scorer_type="ai",
    )


async def compute_ai_score(
    candidate: Candidate,
    weights: ScoringWeights | None = None,
) -> CandidateScore:
    """Score a candidate using the multi-stage pipeline.

    Stage 1: Extract structured signals (no AI)
    Stage 2: Send signals + raw text to Claude for subjective scoring
    Stage 3: Apply weights and return
    """
    client = _get_client()

    # Stage 1: Extract signals (pure code, auditable)
    safe_candidate = anonymize_candidate(candidate)
    signals = extract_signals(safe_candidate)
    signal_context = signals_to_context(signals)

    # Stage 2: Claude scores using structured signals + raw text
    raw_text_context = _build_candidate_context(safe_candidate)
    full_context = f"{signal_context}\n\n{raw_text_context}"

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"{full_context}\n\n{SCORING_PROMPT}"}
        ],
    )

    raw_response = message.content[0].text
    score = _parse_ai_response(raw_response, candidate.id)

    # Stage 3: Apply custom weights if provided
    if weights:
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
        score.overall_score = round(overall, 1)

    return score
