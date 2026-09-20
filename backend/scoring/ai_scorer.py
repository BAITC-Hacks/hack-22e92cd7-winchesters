"""Claude-powered AI scorer — multi-stage pipeline.

Stage 1: signal_extractor.py extracts structured facts (no AI, pure code)
Stage 2: Claude receives pre-extracted signals + raw essay/interview text and
         scores the subjective dimensions
Stage 3: Scores are combined deterministically under committee weights

This means the committee can inspect extracted signals independently of scores,
AI scoring is grounded in verifiable facts, and each score traces to evidence.

Note on scope: these five dimensions are the Stage-1 construct space. Task LED-04
replaces them with the client's nine competencies on three BARS levels. What
changed here (FND-01..03, FND-06) is how the call is made, not yet what is asked.
"""

from __future__ import annotations

from backend import llm, settings
from backend.models import (
    Candidate,
    CandidateScore,
    Confidence,
    DimensionScore,
    ScoringWeights,
)
from backend.privacy import anonymize_candidate
from backend.scoring.aggregator import recompute_overall
from backend.scoring.signal_extractor import extract_signals, signals_to_context

DIMENSION_NAMES = [
    "academic_strength",
    "leadership_potential",
    "motivation_values",
    "growth_trajectory",
    "communication",
]

# The recommendation vocabulary the baseline scorer and the dashboard already
# use. The old prompt asked for this set in prose and a different set
# ("shortlist / review / decline") in its JSON template, so AI-scored candidates
# came back with a label the UI could not read. The enum settles it.
RECOMMENDATIONS = ["recommend", "consider", "needs attention"]

SCORING_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["dimensions", "recommendation", "summary"],
    "properties": {
        "dimensions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "dimension",
                    "score",
                    "confidence",
                    "explanation",
                    "evidence_quotes",
                    "positive_factors",
                    "concerns",
                ],
                "properties": {
                    "dimension": {"type": "string", "enum": DIMENSION_NAMES},
                    "score": {"type": "number"},
                    "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
                    "explanation": {"type": "string"},
                    "evidence_quotes": {"type": "array", "items": {"type": "string"}},
                    "positive_factors": {"type": "array", "items": {"type": "string"}},
                    "concerns": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "recommendation": {"type": "string", "enum": RECOMMENDATIONS},
        "summary": {"type": "string"},
    },
}


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
- Writing in Kazakh or Russian, or mixing languages within one answer

DO reward candidates for:
- Initiative and self-direction (starting projects, solving real problems)
- Authenticity and depth of reflection in essays
- Evidence of growth and overcoming obstacles
- Impact on others, even at small scale
- Honest self-awareness about weaknesses

If the material does not support a judgment on a dimension, say so plainly in the \
explanation and set confidence to "low". An honest low-confidence score is more \
useful to the committee than a confident guess.
"""


SCORING_PROMPT = """\
Using the pre-extracted signals AND the raw text above, evaluate this candidate across 5 dimensions.

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
1. academic_strength: Use extracted GPA, achievements, skills, languages
2. leadership_potential: Initiative, ownership, impact on others, mobilization evidence
3. motivation_values: Depth of purpose, authenticity, mission alignment (read the essay deeply)
4. growth_trajectory: The DELTA — how far they've come, not just where they are
5. communication: Essay quality, specificity, voice authenticity, interview articulation

Score each dimension from 0 to 100. Provide all five dimensions, an overall \
recommendation, and a 2-3 sentence summary.

Quote only text that appears verbatim in the documents. An empty list of quotes is \
better than a paraphrase presented as a quote.
"""


def _build_candidate_context(candidate: Candidate) -> str:
    """Format raw applicant text as tagged documents for qualitative assessment."""
    return "\n\n".join([
        llm.wrap_document(
            candidate.essay.text,
            "essay",
            candidate.id,
        ),
        llm.wrap_document(
            candidate.interview_transcript,
            "interview_transcript",
            candidate.id,
        ),
        llm.wrap_document(
            candidate.recommendation_summary,
            "recommendation_letter",
            candidate.id,
        ),
    ])


def _dimension_from(payload: dict) -> DimensionScore:
    """Build one dimension score, clamping the model's number into range.

    The structured-outputs schema guarantees the shape and the enum values but
    cannot express a numeric range, so the clamp happens here.
    """
    return DimensionScore(
        dimension=payload["dimension"],
        score=max(0.0, min(float(payload["score"]), 100.0)),
        confidence=Confidence(payload["confidence"]),
        explanation=payload["explanation"],
        evidence_quotes=payload["evidence_quotes"],
        positive_factors=payload["positive_factors"],
        concerns=payload["concerns"],
    )


def _score_from_payload(
    payload: dict,
    candidate_id: str,
    weights: ScoringWeights,
) -> CandidateScore:
    """Turn the validated model payload into a CandidateScore."""
    score = CandidateScore(
        candidate_id=candidate_id,
        dimensions=[_dimension_from(d) for d in payload["dimensions"]],
        overall_score=0.0,
        recommendation=payload["recommendation"],
        summary=payload["summary"],
        scorer_type="ai",
    )
    score.overall_score = recompute_overall(score, weights)
    return score


async def compute_ai_score(
    candidate: Candidate,
    weights: ScoringWeights | None = None,
) -> CandidateScore:
    """Score a candidate using the multi-stage pipeline.

    Stage 1: Extract structured signals (no AI)
    Stage 2: Send signals + tagged raw text to Claude for subjective scoring
    Stage 3: Combine under committee weights, deterministically
    """
    safe_candidate = anonymize_candidate(candidate)
    signals = extract_signals(safe_candidate)

    prompt = "\n\n".join([
        signals_to_context(signals),
        _build_candidate_context(safe_candidate),
        SCORING_PROMPT,
    ])

    payload = await llm.complete_json(
        prompt=prompt,
        schema=SCORING_SCHEMA,
        system=SYSTEM_PROMPT,
        model=settings.MODEL_JUDGE,
    )
    return _score_from_payload(payload, candidate.id, weights or ScoringWeights())
