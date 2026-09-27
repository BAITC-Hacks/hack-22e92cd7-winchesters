"""Attributes kept for auditing and kept out of scoring (task LED-01).

The Stage-1 product fed school type into the score through a hand-written table
(private 75, lyceum 60, public 40, village 25) and then subtracted five points
for every hardship keyword it found in the essay. It was framed as helping the
disadvantaged candidate, but it is still a score computed from background, it
rewards disclosing hardship, and a committee cannot defend "plus twelve because
village" to anyone. It is also the mechanism that failed publicly in the UK in
2020, where a school-level prior moved individual results.

So background leaves the scoring path entirely. It is still collected, because
bias exclusion that is "verifiable on data" requires knowing who the applicants
are, but it lives here, is shown to humans as context, and is joined to scores
only when computing an audit.

Nothing in this module may be imported by a scorer. The test suite asserts it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.models import Candidate

# Features that must never reach a model prompt or a weighted sum, with the
# reason each one is barred. The fairness audit renders this list so the
# committee can see the commitment rather than take it on trust (task INP-04).
EXCLUDED_FROM_SCORING: dict[str, str] = {
    "school_type": "background; a proxy for region and family income",
    "region": "protected: the client forbids penalising region",
    "settlement_type": "urban or rural is background, not behaviour",
    "family_income": "protected; Foundation eligibility is a committee policy step",
    "foundation_eligible": "a declared status assessed by humans, never inferred",
    "application_language": "protected: language must not change a score",
    "code_switching": "mixing Kazakh, Russian and English is normal, not a signal",
    "applicant_name": "identity; also a well-documented bias vector in LLM judging",
    "gender": "protected",
    "gpa": "the client states grades do not measure what this selection is for",
    "essay_length": "length rewards verbosity and penalises agglutinative Kazakh",
    "speech_rate": "manner of speech",
    "pause_ratio": "manner of speech",
    "filler_ratio": "register and dialect, not competence",
    "avg_word_length": "a language-identification feature, not a competence signal",
    "hapax_ratio": "morphology, inflated by Kazakh and Russian word forms",
    "audio_quality": "measures the applicant's microphone, i.e. income",
}


@dataclass
class ProtectedAttributes:
    """What we record about background, for audits only.

    Every field is self-declared on the application form. Nothing here is
    inferred from the applicant's writing, because inferring hardship or family
    status from an essay is both unreliable and an invitation to game the form.
    """

    applicant_ref: str
    school_type: str = ""
    application_language: str = ""
    languages_spoken: list[str] = field(default_factory=list)
    # Left empty until the application form collects them (task INP-01).
    region: str = ""
    settlement_type: str = ""
    foundation_eligible: bool | None = None
    gender: str = ""


def extract(candidate: Candidate) -> ProtectedAttributes:
    """Pull background attributes out of an application for the audit table."""
    return ProtectedAttributes(
        applicant_ref=candidate.id,
        school_type=candidate.application.education.school_type,
        languages_spoken=list(candidate.application.languages),
    )


def find_protected_markers(text: str) -> list[str]:
    """Return any background marker that appears in text meant for a scorer.

    Used by the tests, and by the bias probe later, to prove that what reaches
    the model carries no school type. It is a literal search, so it catches the
    structured field values rather than every possible mention in prose; a
    candidate writing "my village school" in their own essay is their own voice
    and stays.
    """
    haystack = text.casefold()
    markers = ["private", "international", "lyceum", "gymnasium", "specialized", "village school"]
    return [marker for marker in markers if f"school type: {marker}" in haystack]
