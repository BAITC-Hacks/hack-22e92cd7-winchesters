"""Stage 1: what the application actually contains (task LED-01).

This module used to do two jobs. It collected facts, which is useful, and it
also judged them with English keyword banks and a school-type advantage table,
which was the product's worst defect. Judging is gone from here. What remains is
a statement of what material exists, so the committee can see the inputs
separately from any assessment of them, and so a missing source is visible as
missing rather than silently scored as weak.

Two deletions are worth naming, because someone will be tempted to put them
back:

- The keyword banks ("started", "founded", "overcome", "passion") only ever
  matched English. Seven of the sixteen demo applications are written in Kazakh
  or Russian, and for those every bank returned nothing, so the pipeline rated
  them lower for writing in their own language. That is the exact bias the
  client says must be verifiably absent.
- The growth delta was `current_level - starting_level`, where the starting
  level came from a table keyed on school type and was pushed down another five
  points for each hardship word found in the essay. See
  `protected_attributes.py` for why that had to go.

Growth is a real thing to assess. It is assessed from what the applicant
describes doing over time, by the evidence pipeline in `backend/ledger/`, not by
arithmetic on their background.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.models import Candidate


@dataclass
class ApplicationFacts:
    """Structured entries the applicant filled in, counted, not judged."""

    achievement_count: int = 0
    achievements: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    language_count: int = 0
    extracurricular_count: int = 0
    # Role labels exactly as written, in whatever language. The old code compared
    # them against an English set, so "президент" and "ұйымдастырушы" scored zero.
    roles: list[str] = field(default_factory=list)
    project_count: int = 0
    projects_with_described_impact: list[str] = field(default_factory=list)
    sustained_activities: list[str] = field(default_factory=list)


@dataclass
class SourceAvailability:
    """Which artifacts exist. A missing source is a gap, never a low score."""

    has_essay: bool = False
    essay_word_count: int = 0
    has_interview: bool = False
    has_recommendation: bool = False
    has_video_transcript: bool = False

    def missing(self) -> list[str]:
        present = {
            "essay": self.has_essay,
            "interview": self.has_interview,
            "recommendation": self.has_recommendation,
            "video": self.has_video_transcript,
        }
        return [name for name, exists in present.items() if not exists]


@dataclass
class ExtractedSignals:
    """Everything known about an application before anything is assessed."""

    candidate_id: str
    facts: ApplicationFacts = field(default_factory=ApplicationFacts)
    availability: SourceAvailability = field(default_factory=SourceAvailability)


SUSTAINED_MONTHS = 24


def _facts_of(candidate: Candidate) -> ApplicationFacts:
    application = candidate.application
    return ApplicationFacts(
        achievement_count=len(application.education.academic_achievements),
        achievements=list(application.education.academic_achievements),
        skills=list(application.skills),
        language_count=len(application.languages),
        extracurricular_count=len(application.extracurriculars),
        roles=[f"{ec.activity}: {ec.role}" for ec in application.extracurriculars],
        project_count=len(application.projects),
        projects_with_described_impact=[
            f"{p.name}: {p.impact}" for p in application.projects if p.impact.strip()
        ],
        sustained_activities=[
            f"{ec.activity} ({ec.duration_months} months)"
            for ec in application.extracurriculars
            if ec.duration_months >= SUSTAINED_MONTHS
        ],
    )


def _availability_of(candidate: Candidate) -> SourceAvailability:
    essay = candidate.essay.text.strip()
    return SourceAvailability(
        has_essay=bool(essay),
        essay_word_count=len(essay.split()),
        has_interview=bool(candidate.interview_transcript.strip()),
        has_recommendation=bool(candidate.recommendation_summary.strip()),
        has_video_transcript=bool(candidate.video_transcript.strip()),
    )


def extract_signals(candidate: Candidate) -> ExtractedSignals:
    """Collect the facts of an application. Pure computation, no judgement."""
    return ExtractedSignals(
        candidate_id=candidate.id,
        facts=_facts_of(candidate),
        availability=_availability_of(candidate),
    )


def signals_to_context(signals: ExtractedSignals) -> str:
    """Render the facts for a model prompt.

    School type, region, language and GPA are deliberately absent. The model is
    asked to read behaviour, and it cannot weigh a background it never sees.
    """
    facts = signals.facts
    availability = signals.availability
    missing = availability.missing()

    lines = [
        "=== APPLICATION FACTS ===",
        "",
        f"Achievements ({facts.achievement_count}): {', '.join(facts.achievements) or 'none listed'}",
        f"Skills: {', '.join(facts.skills) or 'none listed'}",
        f"Languages listed: {facts.language_count}",
        "",
        f"Extracurriculars ({facts.extracurricular_count}):",
        *(f"  - {role}" for role in facts.roles or ["  (none listed)"]),
        "",
        f"Projects ({facts.project_count}):",
        *(f"  - {p}" for p in facts.projects_with_described_impact or ["  (none with described impact)"]),
        "",
        f"Sustained two years or more: {', '.join(facts.sustained_activities) or 'none listed'}",
        "",
        "=== SOURCES AVAILABLE ===",
        f"Essay: {'yes' if availability.has_essay else 'no'}",
        f"Interview transcript: {'yes' if availability.has_interview else 'no'}",
        f"Recommendation letter: {'yes' if availability.has_recommendation else 'no'}",
        f"Video transcript: {'yes' if availability.has_video_transcript else 'no'}",
    ]
    if missing:
        lines += [
            "",
            f"Missing sources: {', '.join(missing)}. Assess only what is present, and "
            "say a dimension cannot be assessed rather than inferring it from absence.",
        ]
    return "\n".join(lines)
