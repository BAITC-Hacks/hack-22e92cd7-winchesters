"""The AI scorer produces a well-formed score without touching the API.

Every Claude call is replaced with a stub, so these tests pin the parts we own:
the prompt we build, the clamping we apply, and the recommendation vocabulary
the dashboard can actually read.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from backend import llm
from backend.models import Candidate, ScoringWeights
from backend.scoring import ai_scorer

DATA = pathlib.Path(__file__).resolve().parents[1] / "backend" / "data" / "candidates.json"


def _candidate(index: int = 0) -> Candidate:
    return Candidate(**json.loads(DATA.read_text(encoding="utf-8"))[index])


def _payload(score: float = 72.0, recommendation: str = "recommend") -> dict:
    return {
        "dimensions": [
            {
                "dimension": name,
                "score": score,
                "confidence": "medium",
                "explanation": "grounded in the extracted signals",
                "evidence_quotes": ["I started a tutoring program"],
                "positive_factors": ["initiative"],
                "concerns": [],
            }
            for name in ai_scorer.DIMENSION_NAMES
        ],
        "recommendation": recommendation,
        "summary": "Strong evidence of initiative.",
    }


@pytest.mark.asyncio
async def test_score_is_well_formed_and_uses_committee_weights(monkeypatch):
    captured = {}

    async def fake_complete_json(prompt, schema, system="", model=""):
        captured["prompt"] = prompt
        captured["schema"] = schema
        captured["model"] = model
        return _payload()

    monkeypatch.setattr(llm, "complete_json", fake_complete_json)

    score = await ai_scorer.compute_ai_score(_candidate(), ScoringWeights())

    assert score.scorer_type == "ai"
    assert len(score.dimensions) == 5
    # Weights sum to 1, so a flat 72 on every dimension is a 72 overall.
    assert score.overall_score == pytest.approx(72.0, abs=0.1)
    assert captured["schema"] is ai_scorer.SCORING_SCHEMA


@pytest.mark.asyncio
async def test_out_of_range_scores_are_clamped_not_trusted(monkeypatch):
    """The schema cannot express a numeric bound, so code has to."""

    async def fake_complete_json(prompt, schema, system="", model=""):
        return _payload(score=140.0)

    monkeypatch.setattr(llm, "complete_json", fake_complete_json)
    score = await ai_scorer.compute_ai_score(_candidate())

    assert all(0 <= d.score <= 100 for d in score.dimensions)
    assert score.overall_score <= 100


@pytest.mark.asyncio
async def test_recommendation_matches_the_vocabulary_the_dashboard_reads(monkeypatch):
    """The old prompt asked for two different vocabularies and the UI saw the wrong one."""

    async def fake_complete_json(prompt, schema, system="", model=""):
        return _payload(recommendation="needs attention")

    monkeypatch.setattr(llm, "complete_json", fake_complete_json)
    score = await ai_scorer.compute_ai_score(_candidate())

    assert score.recommendation in ai_scorer.RECOMMENDATIONS
    assert "shortlist" not in str(ai_scorer.SCORING_SCHEMA)
    assert "decline" not in str(ai_scorer.SCORING_SCHEMA)


@pytest.mark.asyncio
async def test_applicant_text_reaches_the_model_only_inside_documents(monkeypatch):
    captured = {}

    async def fake_complete_json(prompt, schema, system="", model=""):
        captured["prompt"] = prompt
        return _payload()

    monkeypatch.setattr(llm, "complete_json", fake_complete_json)
    candidate = _candidate()
    await ai_scorer.compute_ai_score(candidate)

    prompt = captured["prompt"]
    assert '<document source="essay"' in prompt
    assert '<document source="interview_transcript"' in prompt
    # Instructions sit after the data, which is where long-context prompts want them.
    assert prompt.index("<document") < prompt.index("DIMENSIONS:")


@pytest.mark.asyncio
async def test_names_are_stripped_before_the_prompt_is_built(monkeypatch):
    captured = {}

    async def fake_complete_json(prompt, schema, system="", model=""):
        captured["prompt"] = prompt
        return _payload()

    monkeypatch.setattr(llm, "complete_json", fake_complete_json)
    candidate = _candidate()
    await ai_scorer.compute_ai_score(candidate)

    assert candidate.name not in captured["prompt"]
