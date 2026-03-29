"""Stage 1: Structured signal extraction from candidate data.

Extracts concrete, verifiable facts and qualitative signals from a candidate's
application before any scoring happens. This makes the pipeline auditable —
the committee can see exactly WHAT was extracted, not just the final score.

BEFORE (old approach):
    Candidate JSON → one Claude call → scores + explanations (black box)

AFTER (new approach):
    Candidate JSON → extract_signals() → structured facts
                  → Claude scores ONLY subjective dimensions using those facts
                  → explanations reference specific extracted signals
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass, field

from backend.models import Candidate


# ── Signal containers ──────────────────────────────────────────────


@dataclass
class AcademicSignals:
    gpa: float = 0.0
    gpa_percentile_estimate: str = ""  # "top 5%", "above average", etc.
    achievement_count: int = 0
    achievements: list[str] = field(default_factory=list)
    skills_count: int = 0
    skills: list[str] = field(default_factory=list)
    language_count: int = 0
    languages: list[str] = field(default_factory=list)
    school_type: str = ""


@dataclass
class LeadershipSignals:
    leadership_roles: list[str] = field(default_factory=list)
    project_count: int = 0
    projects_with_impact: list[str] = field(default_factory=list)
    initiative_keywords_found: list[str] = field(default_factory=list)
    people_mobilized: bool = False  # mentions of team, organized others, etc.


@dataclass
class GrowthSignals:
    """Trajectory signals — measures the DELTA, not the snapshot.

    The key insight: we estimate a 'starting_level' and 'current_level'
    to measure how far the candidate has come. This is ADDITIVE — we don't
    penalize privilege, we give bonus credit for overcoming adversity.

    Example:
        Harvard student + great projects = high current_level = good score
        Village student + great projects = high current_level + large delta = higher score on THIS dimension
        Harvard student + no initiative = high starting but low current = low score
    """
    starting_level: float = 50.0  # 0-100, estimated baseline advantage
    current_level: float = 50.0   # 0-100, where they are now
    delta: float = 0.0            # current - starting (the growth)
    adversity_indicators: list[str] = field(default_factory=list)
    growth_evidence: list[str] = field(default_factory=list)
    sustained_commitments: list[str] = field(default_factory=list)
    self_started_count: int = 0


@dataclass
class CommunicationSignals:
    essay_word_count: int = 0
    avg_sentence_length: float = 0.0
    sentence_length_variance: float = 0.0
    vocabulary_richness: float = 0.0  # type-token ratio
    has_interview: bool = False
    interview_word_count: int = 0
    specificity_score: float = 0.0  # ratio of concrete details (names, numbers, places)


@dataclass
class MotivationSignals:
    mission_alignment_keywords: list[str] = field(default_factory=list)
    purpose_depth: str = ""  # "vague", "moderate", "deep"
    has_interview: bool = False
    has_recommendation: bool = False
    concrete_future_plans: bool = False


@dataclass
class ExtractedSignals:
    """All signals for one candidate, fully structured and auditable."""
    candidate_id: str
    academic: AcademicSignals = field(default_factory=AcademicSignals)
    leadership: LeadershipSignals = field(default_factory=LeadershipSignals)
    growth: GrowthSignals = field(default_factory=GrowthSignals)
    communication: CommunicationSignals = field(default_factory=CommunicationSignals)
    motivation: MotivationSignals = field(default_factory=MotivationSignals)


# ── Keyword banks ──────────────────────────────────────────────────

INITIATIVE_KEYWORDS = [
    "started", "created", "built", "founded", "launched", "organized",
    "initiated", "invented", "developed", "designed", "led",
]

ADVERSITY_KEYWORDS = [
    "village", "rural", "public school", "single parent", "single mother",
    "single father", "financial", "poverty", "couldn't afford",
    "part-time work", "family business", "had to work", "first in my family",
    "no resources", "limited access", "despite",
]

GROWTH_KEYWORDS = [
    "overcome", "challenge", "struggle", "difficult", "failure", "failed",
    "learned", "grew", "improved", "despite", "adversity", "obstacle",
    "started from", "taught myself", "self-taught", "went from",
    "used to be", "transformed", "changed", "progress",
]

MOTIVATION_KEYWORDS = [
    "passion", "mission", "impact", "change", "community", "future",
    "believe", "dream", "committed", "dedicated", "driven", "purpose",
    "contribute", "solve", "make a difference", "help others",
]

SPECIFICITY_PATTERNS = [
    r'\b\d{4}\b',           # years (2023, etc.)
    r'\b\d+\s*(people|students|participants|members)',  # numbers of people
    r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b',
    r'\b(?:Mr\.|Mrs\.|Ms\.)\s+\w+',  # teacher names
    r'(?:school|city|village|town)\s+(?:of\s+)?\w+',  # place names
]

# School types mapped to estimated starting advantage (0-100).
# Higher = more privilege/resources available.
# This is NOT a penalty — it's used to compute the growth delta.
SCHOOL_ADVANTAGE = {
    "private": 75,
    "international": 80,
    "lyceum": 60,
    "gymnasium": 60,
    "specialized": 55,
    "public": 40,
    "village": 25,
    "rural": 25,
}


# ── Extraction functions ──────────────────────────────────────────


def _find_keywords(text: str, keywords: list[str]) -> list[str]:
    """Return which keywords appear in text."""
    text_lower = text.lower()
    return [kw for kw in keywords if kw in text_lower]


def _count_specificity(text: str) -> float:
    """Count concrete details (names, numbers, dates, places) per 100 words."""
    words = text.split()
    if not words:
        return 0.0
    matches = sum(len(re.findall(p, text, re.IGNORECASE)) for p in SPECIFICITY_PATTERNS)
    return (matches / len(words)) * 100


def extract_signals(candidate: Candidate) -> ExtractedSignals:
    """Extract all structured signals from a candidate. Pure computation, no AI calls."""
    signals = ExtractedSignals(candidate_id=candidate.id)
    app = candidate.application
    essay_text = candidate.essay.text
    all_text = f"{essay_text} {candidate.interview_transcript} {candidate.recommendation_summary}"

    # ── Academic ──
    signals.academic = AcademicSignals(
        gpa=app.education.gpa,
        gpa_percentile_estimate=(
            "top 5%" if app.education.gpa >= 3.9
            else "top 15%" if app.education.gpa >= 3.7
            else "above average" if app.education.gpa >= 3.0
            else "below average"
        ),
        achievement_count=len(app.education.academic_achievements),
        achievements=list(app.education.academic_achievements),
        skills_count=len(app.skills),
        skills=list(app.skills),
        language_count=len(app.languages),
        languages=list(app.languages),
        school_type=app.education.school_type,
    )

    # ── Leadership ──
    leader_role_names = {"leader", "president", "founder", "captain", "co-founder",
                         "organizer", "coordinator", "editor-in-chief", "secretary-general",
                         "editor", "creator", "director"}
    leadership_roles = [
        f"{ec.activity} ({ec.role})"
        for ec in app.extracurriculars
        if ec.role.lower() in leader_role_names
    ]
    projects_with_impact = [
        f"{p.name}: {p.impact[:80]}"
        for p in app.projects
        if len(p.impact) > 20
    ]
    initiative_kws = _find_keywords(all_text, INITIATIVE_KEYWORDS)
    people_words = _find_keywords(all_text, [
        "team", "organized others", "recruited", "mobilized", "mentored",
        "taught others", "brought together", "gathered",
    ])
    signals.leadership = LeadershipSignals(
        leadership_roles=leadership_roles,
        project_count=len(app.projects),
        projects_with_impact=projects_with_impact,
        initiative_keywords_found=initiative_kws,
        people_mobilized=len(people_words) > 0,
    )

    # ── Growth / Trajectory ──
    school_lower = app.education.school_type.lower()
    starting = 50.0
    for key, advantage in SCHOOL_ADVANTAGE.items():
        if key in school_lower:
            starting = float(advantage)
            break

    adversity = _find_keywords(all_text, ADVERSITY_KEYWORDS)
    if adversity:
        # Each adversity indicator lowers starting level (they had LESS to start with)
        starting = max(starting - len(adversity) * 5, 10)

    # Current level: based on what they've achieved
    current = 30.0  # base
    current += min(len(leadership_roles) * 10, 30)
    current += min(len(app.projects) * 8, 24)
    current += min(app.education.gpa / 4.0 * 16, 16)
    growth_evidence = _find_keywords(all_text, GROWTH_KEYWORDS)
    current += min(len(growth_evidence) * 3, 15)

    # Self-started activities
    self_started = [
        ec for ec in app.extracurriculars
        if ec.role.lower() in ("founder", "creator", "co-founder")
    ]

    sustained = [
        f"{ec.activity} ({ec.duration_months} months)"
        for ec in app.extracurriculars
        if ec.duration_months >= 24
    ]

    delta = max(current - starting, 0)

    signals.growth = GrowthSignals(
        starting_level=round(starting, 1),
        current_level=round(min(current, 100), 1),
        delta=round(delta, 1),
        adversity_indicators=adversity,
        growth_evidence=growth_evidence,
        sustained_commitments=sustained,
        self_started_count=len(self_started),
    )

    # ── Communication ──
    words = essay_text.split()
    sentences = [s.strip() for s in re.split(r'[.!?]+', essay_text) if s.strip()]
    sent_lengths = [len(s.split()) for s in sentences] if sentences else [0]
    unique_words = set(w.lower() for w in words)

    interview_words = candidate.interview_transcript.split() if candidate.interview_transcript else []

    signals.communication = CommunicationSignals(
        essay_word_count=len(words),
        avg_sentence_length=round(statistics.mean(sent_lengths), 1) if sent_lengths else 0,
        sentence_length_variance=round(statistics.variance(sent_lengths), 1) if len(sent_lengths) > 1 else 0,
        vocabulary_richness=round(len(unique_words) / len(words), 3) if words else 0,
        has_interview=bool(candidate.interview_transcript),
        interview_word_count=len(interview_words),
        specificity_score=round(_count_specificity(essay_text), 2),
    )

    # ── Motivation ──
    motivation_kws = _find_keywords(all_text, MOTIVATION_KEYWORDS)
    future_kws = _find_keywords(all_text, [
        "plan to", "want to build", "goal is", "i will", "intend to",
        "my dream is", "after graduation", "in the future",
    ])
    depth = (
        "deep" if len(motivation_kws) >= 6
        else "moderate" if len(motivation_kws) >= 3
        else "vague"
    )
    signals.motivation = MotivationSignals(
        mission_alignment_keywords=motivation_kws,
        purpose_depth=depth,
        has_interview=bool(candidate.interview_transcript),
        has_recommendation=bool(candidate.recommendation_summary),
        concrete_future_plans=len(future_kws) > 0,
    )

    return signals


def signals_to_context(signals: ExtractedSignals) -> str:
    """Convert extracted signals into a readable text block for the AI scorer.

    This replaces the raw candidate data — the AI now sees structured facts
    instead of raw text, making its scoring more grounded and auditable.
    """
    s = signals
    lines = [
        f"=== EXTRACTED SIGNALS FOR {s.candidate_id} ===",
        "",
        "ACADEMIC:",
        f"  GPA: {s.academic.gpa}/4.0 ({s.academic.gpa_percentile_estimate})",
        f"  School type: {s.academic.school_type}",
        f"  Achievements ({s.academic.achievement_count}): {', '.join(s.academic.achievements) or 'None'}",
        f"  Skills ({s.academic.skills_count}): {', '.join(s.academic.skills) or 'None'}",
        f"  Languages ({s.academic.language_count}): {', '.join(s.academic.languages) or 'None'}",
        "",
        "LEADERSHIP:",
        f"  Leadership roles: {', '.join(s.leadership.leadership_roles) or 'None'}",
        f"  Projects ({s.leadership.project_count}): {'; '.join(s.leadership.projects_with_impact) or 'None with described impact'}",
        f"  Initiative keywords detected: {', '.join(s.leadership.initiative_keywords_found) or 'None'}",
        f"  Evidence of mobilizing others: {'Yes' if s.leadership.people_mobilized else 'No'}",
        "",
        "GROWTH TRAJECTORY:",
        f"  Estimated starting advantage: {s.growth.starting_level}/100 (based on school type + adversity signals)",
        f"  Current achievement level: {s.growth.current_level}/100",
        f"  Growth delta: +{s.growth.delta} (how far they've come)",
        f"  Adversity indicators: {', '.join(s.growth.adversity_indicators) or 'None detected'}",
        f"  Growth evidence in text: {', '.join(s.growth.growth_evidence) or 'None detected'}",
        f"  Sustained commitments (2+ years): {', '.join(s.growth.sustained_commitments) or 'None'}",
        f"  Self-started activities: {s.growth.self_started_count}",
        "",
        "COMMUNICATION:",
        f"  Essay: {s.communication.essay_word_count} words, avg sentence {s.communication.avg_sentence_length} words",
        f"  Sentence length variance: {s.communication.sentence_length_variance} (higher = more natural variety)",
        f"  Vocabulary richness (TTR): {s.communication.vocabulary_richness}",
        f"  Specificity score: {s.communication.specificity_score} (concrete names/dates/numbers per 100 words)",
        f"  Interview: {'Yes (' + str(s.communication.interview_word_count) + ' words)' if s.communication.has_interview else 'Not available'}",
        "",
        "MOTIVATION:",
        f"  Mission-aligned keywords: {', '.join(s.motivation.mission_alignment_keywords) or 'None'}",
        f"  Purpose depth: {s.motivation.purpose_depth}",
        f"  Concrete future plans: {'Yes' if s.motivation.concrete_future_plans else 'No'}",
        f"  Recommendation letter: {'Yes' if s.motivation.has_recommendation else 'No'}",
    ]
    return "\n".join(lines)
