from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


# ── Candidate Input Models ──────────────────────────────────────────


class Education(BaseModel):
    school_type: str = Field(description="e.g. public, private, lyceum, gymnasium")
    gpa: float = Field(ge=0, le=4.0)
    academic_achievements: list[str] = Field(default_factory=list)
    years_of_study: int = 11


class Extracurricular(BaseModel):
    activity: str
    duration_months: int
    role: str = Field(description="e.g. member, organizer, leader, founder")


class Project(BaseModel):
    name: str
    role: str
    impact: str = ""


class Essay(BaseModel):
    prompt: str
    text: str
    word_count: int = 0

    def model_post_init(self, __context: object) -> None:
        if self.word_count == 0:
            self.word_count = len(self.text.split())


class Application(BaseModel):
    education: Education
    extracurriculars: list[Extracurricular] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)


class Candidate(BaseModel):
    id: str
    name: str
    age: int = 17
    application: Application
    essay: Essay
    interview_transcript: str = ""
    recommendation_summary: str = ""
    video_link: str = ""
    video_transcript: str = ""


# ── Scoring Models ──────────────────────────────────────────────────


class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DimensionScore(BaseModel):
    dimension: str
    score: float = Field(ge=0, le=100)
    confidence: Confidence = Confidence.MEDIUM
    explanation: str = ""
    evidence_quotes: list[str] = Field(default_factory=list)
    positive_factors: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)


class StylometryMetrics(BaseModel):
    """Quantitative text features computed without AI — auditable and reproducible."""
    ttr: float = Field(0.0, description="Type-token ratio (vocabulary richness)")
    avg_sentence_length: float = 0.0
    sentence_length_variance: float = 0.0
    avg_word_length: float = 0.0
    formality_ratio: float = Field(0.0, description="Ratio of formal/filler phrases")
    hapax_ratio: float = Field(0.0, description="Ratio of words used only once")
    essay_interview_vocab_overlap: float = Field(
        0.0, description="Jaccard similarity between essay and interview vocabulary"
    )


class AIDetectionResult(BaseModel):
    authenticity_score: float = Field(ge=0, le=100, description="100 = fully authentic")
    flags: list[str] = Field(default_factory=list)
    explanation: str = ""
    stylometry: StylometryMetrics | None = None


class VideoAnalysisResult(BaseModel):
    """Result of analyzing a candidate's video presentation transcript."""
    transcript: str = ""
    language_detected: str = ""
    authenticity_match: float = Field(0, ge=0, le=100, description="How well video voice matches essay voice. 100 = perfect match")
    motivation_score: float = Field(0, ge=0, le=100)
    key_themes: list[str] = Field(default_factory=list)
    growth_signals: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    summary: str = ""
    is_mock: bool = False


class CandidateScore(BaseModel):
    candidate_id: str
    dimensions: list[DimensionScore]
    overall_score: float = Field(ge=0, le=100)
    ai_detection: AIDetectionResult | None = None
    recommendation: str = Field(description="shortlist / review / decline")
    summary: str = ""
    scorer_type: str = Field(description="baseline or ai")


# ── Ranking & Comparison ────────────────────────────────────────────


class RankedCandidate(BaseModel):
    rank: int
    candidate: Candidate
    ai_score: CandidateScore | None = None
    baseline_score: CandidateScore | None = None


class ScoringWeights(BaseModel):
    academic_strength: float = 0.15
    leadership_potential: float = 0.25
    motivation_values: float = 0.25
    growth_trajectory: float = 0.20
    communication: float = 0.15


class CommitteeOverride(BaseModel):
    candidate_id: str
    dimension: str
    override_score: float = Field(ge=0, le=100)
    note: str = ""
