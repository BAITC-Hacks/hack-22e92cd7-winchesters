"""Rule-based baseline scorer for comparison with AI scorer.

Simple heuristics: GPA thresholds, keyword matching, achievement counting.
Intentionally naive to demonstrate improvement from the AI approach.

The growth_trajectory dimension now uses trajectory scoring via signal_extractor,
measuring the DELTA (how far the candidate has come) rather than just a snapshot
of where they are today.
"""

from __future__ import annotations

import re

from backend.models import (
    AIDetectionResult,
    Candidate,
    CandidateScore,
    Confidence,
    DimensionScore,
    ScoringWeights,
)
from backend.scoring.signal_extractor import extract_signals

LEADERSHIP_KEYWORDS = [
    "leader", "president", "founder", "captain", "organizer",
    "coordinator", "director", "editor-in-chief", "secretary-general",
    "co-founder", "lead", "initiative", "started", "created", "built",
]

MOTIVATION_KEYWORDS = [
    "passion", "mission", "impact", "change", "community", "future",
    "believe", "dream", "committed", "dedicated", "driven", "purpose",
]

GROWTH_KEYWORDS = [
    "overcome", "challenge", "struggle", "difficult", "failure", "failed",
    "learned", "grew", "improved", "despite", "adversity", "obstacle",
]


def _count_keywords(text: str, keywords: list[str]) -> int:
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


def score_academic(candidate: Candidate) -> DimensionScore:
    edu = candidate.application.education
    score = 0.0
    factors: list[str] = []
    concerns: list[str] = []

    # GPA component (0-40)
    gpa_score = min((edu.gpa / 4.0) * 40, 40)
    score += gpa_score
    if edu.gpa >= 3.8:
        factors.append(f"Strong GPA: {edu.gpa}")
    elif edu.gpa < 3.0:
        concerns.append(f"Below-average GPA: {edu.gpa}")

    # Achievements (0-35, 7 pts each up to 5)
    n_achievements = len(edu.academic_achievements)
    achievement_score = min(n_achievements * 7, 35)
    score += achievement_score
    if n_achievements >= 3:
        factors.append(f"{n_achievements} academic achievements")
    elif n_achievements == 0:
        concerns.append("No recorded academic achievements")

    # Skills breadth (0-15, 3 pts each up to 5)
    n_skills = len(candidate.application.skills)
    score += min(n_skills * 3, 15)

    # Languages (0-10, bonus for multilingual)
    n_lang = len(candidate.application.languages)
    score += min((n_lang - 1) * 5, 10)
    if n_lang >= 3:
        factors.append(f"Multilingual: {n_lang} languages")

    return DimensionScore(
        dimension="academic_strength",
        score=min(score, 100),
        confidence=Confidence.HIGH,
        explanation=f"Rule-based: GPA={edu.gpa}, {n_achievements} achievements, {n_skills} skills, {n_lang} languages",
        positive_factors=factors,
        concerns=concerns,
    )


def score_leadership(candidate: Candidate) -> DimensionScore:
    score = 0.0
    factors: list[str] = []
    concerns: list[str] = []

    # Leadership roles in extracurriculars (0-40)
    leader_roles = [
        ec for ec in candidate.application.extracurriculars
        if ec.role.lower() in ("leader", "president", "founder", "captain", "co-founder",
                                "organizer", "coordinator", "editor-in-chief", "secretary-general",
                                "editor", "creator", "director")
    ]
    score += min(len(leader_roles) * 15, 40)
    if leader_roles:
        factors.append(f"{len(leader_roles)} leadership role(s)")

    # Projects initiated (0-30)
    n_projects = len(candidate.application.projects)
    score += min(n_projects * 15, 30)
    if n_projects >= 1:
        factors.append(f"{n_projects} project(s) initiated")
    else:
        concerns.append("No recorded projects")

    # Leadership keywords in essay (0-30)
    kw_count = _count_keywords(candidate.essay.text, LEADERSHIP_KEYWORDS)
    score += min(kw_count * 5, 30)

    if score < 30:
        concerns.append("Limited evidence of leadership activities")

    return DimensionScore(
        dimension="leadership_potential",
        score=min(score, 100),
        confidence=Confidence.MEDIUM,
        explanation=f"Rule-based: {len(leader_roles)} leadership roles, {n_projects} projects, {kw_count} leadership keywords in essay",
        positive_factors=factors,
        concerns=concerns,
    )


def score_motivation(candidate: Candidate) -> DimensionScore:
    """Score motivation with missing data handling.

    BEFORE: no interview = 0 pts for that sub-score, confidence stays LOW.
    AFTER:  no interview = try to compensate by looking for motivation signals
            in essay more heavily, and mark confidence accordingly.
    """
    score = 0.0
    factors: list[str] = []
    concerns: list[str] = []
    missing_sources = 0

    essay = candidate.essay

    # Essay length (0-20)
    if 300 <= essay.word_count <= 1000:
        score += 20
    elif essay.word_count < 150:
        score += 5
        concerns.append(f"Very short essay ({essay.word_count} words)")
    else:
        score += 10

    # Motivation keywords (0-40)
    kw_count = _count_keywords(essay.text, MOTIVATION_KEYWORDS)
    score += min(kw_count * 6, 40)
    if kw_count >= 5:
        factors.append("Strong motivational language")

    # Interview presence (0-20)
    if candidate.interview_transcript:
        score += 20
        factors.append("Interview completed")
    else:
        missing_sources += 1
        concerns.append("No interview on record — motivation assessment relies on essay only")
        # Compensate: look for motivation signals in essay more generously
        extra_kw = _count_keywords(essay.text, [
            "want to", "goal", "plan to", "hope to", "aspire",
            "my dream", "i will", "determined",
        ])
        compensated = min(extra_kw * 4, 12)
        if compensated > 0:
            score += compensated
            factors.append(f"Compensated from essay: {extra_kw} additional motivation signals")

    # Recommendation (0-20)
    if candidate.recommendation_summary:
        score += 20
        factors.append("Has recommendation letter")
    else:
        missing_sources += 1
        concerns.append("No recommendation letter — external validation unavailable")

    # Confidence depends on data completeness
    if missing_sources >= 2:
        confidence = Confidence.LOW
    elif missing_sources == 1:
        confidence = Confidence.LOW
    else:
        confidence = Confidence.MEDIUM

    return DimensionScore(
        dimension="motivation_values",
        score=min(score, 100),
        confidence=confidence,
        explanation=f"Rule-based: {essay.word_count} words, {kw_count} motivation keywords, interview={'yes' if candidate.interview_transcript else 'no'}, recommendation={'yes' if candidate.recommendation_summary else 'no'}{' [incomplete data — confidence reduced]' if missing_sources else ''}",
        positive_factors=factors,
        concerns=concerns,
    )


def score_growth(candidate: Candidate) -> DimensionScore:
    """Trajectory-based growth scoring.

    BEFORE (old approach):
        Counted growth keywords + long activities + projects with impact.
        A privileged candidate with lots of school-assigned projects would
        score the same as a disadvantaged candidate who self-started projects.
        It measured WHAT you have, not HOW FAR you came.

    AFTER (new approach):
        Uses signal_extractor to compute starting_level, current_level, and delta.
        Score = delta_component (how far you grew) + base_component (where you are).
        This is ADDITIVE — nobody is penalized for privilege. But a candidate who
        climbed further gets more credit on THIS specific dimension.

        Example with the formula below (delta_weight=0.6, base_weight=0.4):
        - Village student (start=25, current=75, delta=50):
          score = 50*0.6 + 75*0.4 = 30 + 30 = 60
        - Elite student (start=75, current=85, delta=10):
          score = 10*0.6 + 85*0.4 = 6 + 34 = 40
        - Elite student who also self-started (start=75, current=95, delta=20):
          score = 20*0.6 + 95*0.4 = 12 + 38 = 50

        The elite students still score well overall (high academic, leadership, etc.)
        — this dimension specifically measures growth trajectory.
    """
    factors: list[str] = []
    concerns: list[str] = []

    signals = extract_signals(candidate)
    g = signals.growth

    # Delta component (60% of score): how far they've come
    # Normalized: delta of 50+ = full marks on this component
    delta_component = min(g.delta / 50.0, 1.0) * 60

    # Base component (40% of score): where they are now
    base_component = (g.current_level / 100.0) * 40

    score = delta_component + base_component

    # Bonus for sustained commitments (up to +10)
    sustained_bonus = min(len(g.sustained_commitments) * 5, 10)
    score += sustained_bonus

    # Bonus for self-started initiatives (up to +10)
    self_start_bonus = min(g.self_started_count * 5, 10)
    score += self_start_bonus

    score = min(score, 100)

    # Explain the trajectory
    factors.append(
        f"Growth delta: +{g.delta} (from {g.starting_level} to {g.current_level})"
    )
    if g.adversity_indicators:
        factors.append(
            f"Overcame adversity: {', '.join(g.adversity_indicators[:3])}"
        )
    if g.sustained_commitments:
        factors.append(
            f"{len(g.sustained_commitments)} sustained commitment(s) (2+ years)"
        )
    if g.self_started_count > 0:
        factors.append(f"{g.self_started_count} self-started initiative(s)")
    if g.growth_evidence:
        factors.append(
            f"Growth language in text: {', '.join(g.growth_evidence[:4])}"
        )

    if g.delta < 15:
        concerns.append(
            f"Low growth delta ({g.delta}) — limited evidence of trajectory"
        )
    if not g.growth_evidence:
        concerns.append("No growth-related language found in essay/interview")

    return DimensionScore(
        dimension="growth_trajectory",
        score=round(score, 1),
        confidence=Confidence.MEDIUM,
        explanation=(
            f"Trajectory scoring: starting_level={g.starting_level}, "
            f"current_level={g.current_level}, delta=+{g.delta}. "
            f"Score = delta_component({delta_component:.0f}) + "
            f"base_component({base_component:.0f}) + "
            f"bonuses({sustained_bonus + self_start_bonus})"
        ),
        positive_factors=factors,
        concerns=concerns,
    )


def score_communication(candidate: Candidate) -> DimensionScore:
    """Score communication with missing data handling.

    BEFORE: no interview = 0 pts for interview sub-score, confidence stays MEDIUM.
    AFTER:  no interview = compensate by weighting essay analysis more heavily,
            and reduce confidence to LOW since we can't assess verbal communication.
    """
    score = 0.0
    factors: list[str] = []
    concerns: list[str] = []
    has_interview = bool(candidate.interview_transcript)

    essay = candidate.essay

    # Essay length (0-25, or 0-35 if no interview — essay carries more weight)
    max_essay_pts = 25 if has_interview else 35
    if 400 <= essay.word_count <= 800:
        score += max_essay_pts
        factors.append("Well-structured essay length")
    elif essay.word_count >= 200:
        score += max_essay_pts * 0.6
    else:
        score += 5
        concerns.append("Essay too short for meaningful assessment")

    # Sentence variety (0-25, or 0-30 if no interview)
    sentences = re.split(r'[.!?]+', essay.text)
    sentences = [s.strip() for s in sentences if s.strip()]
    max_variety_pts = 25 if has_interview else 30
    if sentences:
        avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
        if 10 <= avg_len <= 25:
            score += max_variety_pts
        elif avg_len < 10:
            score += max_variety_pts * 0.4
            concerns.append("Very short sentences — may lack depth")
        else:
            score += max_variety_pts * 0.6

    # Interview presence and length (0-25)
    if has_interview:
        interview_words = len(candidate.interview_transcript.split())
        if interview_words > 150:
            score += 25
            factors.append("Detailed interview responses")
        else:
            score += 15
    else:
        concerns.append("No interview — verbal communication not assessed, essay weighted more heavily")

    # Communication-related skills (0-25)
    comm_skills = {"public speaking", "writing", "journalism", "debate",
                   "storytelling", "creative writing", "media literacy"}
    matching = comm_skills & set(s.lower() for s in candidate.application.skills)
    score += min(len(matching) * 12, 25)
    if matching:
        factors.append(f"Communication skills: {', '.join(matching)}")

    confidence = Confidence.MEDIUM if has_interview else Confidence.LOW

    return DimensionScore(
        dimension="communication",
        score=min(score, 100),
        confidence=confidence,
        explanation=f"Rule-based: {essay.word_count}-word essay, {len(sentences)} sentences, interview={'yes' if has_interview else 'no [confidence reduced, essay weighted more]'}",
        positive_factors=factors,
        concerns=concerns,
    )


def compute_baseline_score(
    candidate: Candidate,
    weights: ScoringWeights | None = None,
) -> CandidateScore:
    """Compute a full baseline score for a candidate."""
    if weights is None:
        weights = ScoringWeights()

    dimensions = [
        score_academic(candidate),
        score_leadership(candidate),
        score_motivation(candidate),
        score_growth(candidate),
        score_communication(candidate),
    ]

    weight_map = {
        "academic_strength": weights.academic_strength,
        "leadership_potential": weights.leadership_potential,
        "motivation_values": weights.motivation_values,
        "growth_trajectory": weights.growth_trajectory,
        "communication": weights.communication,
    }

    overall = sum(
        d.score * weight_map.get(d.dimension, 0.2)
        for d in dimensions
    )

    # AI recommendation (advisory only — final decision is always human)
    if overall >= 70:
        recommendation = "recommend"
    elif overall >= 50:
        recommendation = "consider"
    else:
        recommendation = "needs attention"

    return CandidateScore(
        candidate_id=candidate.id,
        dimensions=dimensions,
        overall_score=round(overall, 1),
        recommendation=recommendation,
        summary=f"Baseline score: {overall:.1f}/100. Recommendation: {recommendation}.",
        scorer_type="baseline",
    )
