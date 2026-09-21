"""The evidence ledger contract (task LED-03).

This file is the boundary between the two halves of the product. The platform
side mirrors these shapes as table columns and renders them; the AI side fills
them in. Both owners review a change here, because a change here is a change to
the database and to the committee card at the same time.

The shape exists to make one sentence true: every level the committee sees
decomposes into a behavioural indicator and a quote that is verifiably present
in what the applicant actually wrote or said.

Three properties are deliberate and should not be "simplified" away:

1. `no_evidence` is not `weak`. A rejection defended with "we saw no behaviour
   for indicator X" survives an appeal; one defended with "the model felt weak"
   does not. They are different states and the committee must be able to tell
   them apart.
2. A competency level is *derived* from indicator ratings by a rule that is
   written down and returned alongside the level. The model never hands us a
   competency level directly, so the same evidence always yields the same score.
3. Competencies 8 and 9 (purpose-driven and wounded leadership) carry no AI
   level at all. The methodology owner rates them live. The AI may only surface
   indicator observations and attention flags for a human to verify.
"""

from __future__ import annotations

import unicodedata
from enum import Enum

from pydantic import BaseModel, Field

SCHEMA_VERSION = "led-03.1"


# ── Vocabulary ─────────────────────────────────────────────────────


class Competency(str, Enum):
    """The nine blocks inVision U assesses. Ids are stable; labels are display."""

    MOTIVATION_UNIVERSITY = "motivation_university"
    MOTIVATION_MAJOR = "motivation_major"
    LEADERSHIP_ABILITIES = "leadership_abilities"
    TEAMWORK = "teamwork"
    VALUES = "values"
    PRIOR_EXPERIENCE = "prior_experience"
    INTELLECT = "intellect"
    PURPOSE_DRIVEN_LEADERSHIP = "purpose_driven_leadership"
    WOUNDED_LEADERSHIP = "wounded_leadership"


class Level(str, Enum):
    """The client's three BARS levels, plus the honest fourth state."""

    WEAK = "weak"
    NORMAL = "normal"
    HIGH = "high"
    NO_EVIDENCE = "no_evidence"


class AtolaComponent(str, Enum):
    """Which part of a behavioural story a quote belongs to."""

    ACTION = "action"
    THINKING = "thinking"
    OUTCOME = "outcome"
    LEARNINGS = "learnings"
    APPLICATION = "application"
    NONE = "none"


class Source(str, Enum):
    """Where a quote came from. Kept on every item so a card can link back."""

    ESSAY = "essay"
    WRITTEN_PRESENTATION = "written_presentation"
    VIDEO_TRANSCRIPT = "video_transcript"
    SCENARIO = "scenario"
    INTERVIEW_NOTES = "interview_notes"
    RECOMMENDATION_LETTER = "recommendation_letter"
    IPSATIVE_TEST = "ipsative_test"


class EvidenceStatus(str, Enum):
    """What the evidence does to the indicator it is attached to."""

    PRESENT = "present"           # the behaviour is demonstrated
    CLAIMED_ONLY = "claimed_only"  # asserted, but no situated episode behind it
    CONTRADICTED = "contradicted"  # the material argues against the behaviour
    NOT_ASSESSABLE = "not_assessable"  # source too noisy to read (e.g. low-confidence ASR)


# ── Records ────────────────────────────────────────────────────────


class EvidenceItem(BaseModel):
    """One quote, attached to one indicator.

    `verified` is computed by us, never supplied by the model: it records that
    the quote is literally present in the source text. An unverified quote is
    dropped before rating, which is also what stops text smuggled into an essay
    from becoming evidence about the applicant.
    """

    quote: str = Field(description="Verbatim, in the language the applicant used")
    source: Source
    source_ref: str = Field("", description="Artifact id the quote was taken from")
    char_start: int = -1
    char_end: int = -1
    atola: AtolaComponent = AtolaComponent.NONE
    status: EvidenceStatus = EvidenceStatus.PRESENT
    verified: bool = False
    indicator_hint: str = Field(
        "",
        description=(
            "Which indicator the extraction stage thought this speaks to. A "
            "suggestion carried to the rater for context, never authoritative: "
            "the rater decides what the evidence actually shows."
        ),
    )


class IndicatorRating(BaseModel):
    """One behavioural indicator, the level observed for it, and why."""

    indicator_id: str
    observed_level: Level = Level.NO_EVIDENCE
    evidence: list[EvidenceItem] = Field(default_factory=list)
    note: str = Field("", description="One line, referencing the evidence, not vibes")

    def has_verified_evidence(self) -> bool:
        return any(item.verified for item in self.evidence)


class AttentionFlag(BaseModel):
    """Something a human should look at. Never arithmetic, never a penalty.

    Used for the weak anchors of wounded leadership (blame language, harshness,
    a victim position) and for cross-source inconsistencies. A flag routes to
    the interviewer as "verify live"; it must never move a number.
    """

    code: str
    quote: str = ""
    source: Source | None = None
    explanation: str = ""


class CompetencyRating(BaseModel):
    """One of the nine blocks, as the committee card shows it."""

    competency: Competency
    indicators: list[IndicatorRating] = Field(default_factory=list)
    level: Level | None = Field(
        None,
        description="None when the rubric reserves this competency for humans",
    )
    rule_applied: str = Field("", description="Id of the derivation rule that fired")
    reserved_for_humans: bool = False
    contrastive: str = Field(
        "",
        description="What evidence would be needed for the next level, in anchor wording",
    )
    probe_question: str = Field("", description="Pre-approved ATOLA probe for the interviewer")
    flags: list[AttentionFlag] = Field(default_factory=list)


class CandidateLedger(BaseModel):
    """Everything known about one applicant, as evidence rather than as a score."""

    applicant_ref: str = Field(description="Pseudonymous id; never a name")
    schema_version: str = SCHEMA_VERSION
    rubric_version: str = ""
    model_judge: str = ""
    model_extract: str = ""
    prompt_version: str = ""
    competencies: list[CompetencyRating] = Field(default_factory=list)

    def by_competency(self) -> dict[Competency, CompetencyRating]:
        """Lookup keyed by competency, for views that render a fixed nine rows."""
        return {rating.competency: rating for rating in self.competencies}


# ── Quote verification ─────────────────────────────────────────────


def normalize(text: str) -> str:
    """Fold a string to the form quote matching compares.

    Unicode normalisation matters here: Kazakh and Russian text arrives in both
    composed and decomposed forms depending on the keyboard and the browser, and
    two visually identical strings otherwise fail an exact match.
    """
    folded = unicodedata.normalize("NFC", text or "")
    folded = folded.replace(" ", " ").replace("’", "'").replace("‘", "'")
    folded = folded.replace("“", '"').replace("”", '"')
    return " ".join(folded.split()).casefold()


def verify_quote(quote: str, source_text: str) -> bool:
    """True when the quote really appears in the source.

    This is the injection firewall as much as an anti-hallucination check: an
    instruction the model invented, or one it echoed from somewhere other than
    the applicant's own words, cannot pass.
    """
    if not quote or not quote.strip():
        return False
    return normalize(quote) in normalize(source_text)


def locate_quote(quote: str, source_text: str) -> tuple[int, int]:
    """Character span of the quote in the raw source, or (-1, -1) if absent.

    Best effort on the raw text so the front end can highlight; verification
    itself always uses the normalised comparison above.
    """
    if not quote:
        return (-1, -1)
    index = source_text.find(quote)
    if index >= 0:
        return (index, index + len(quote))
    return (-1, -1)


# ── Deterministic level derivation ─────────────────────────────────

# Read top to bottom; the first rule that matches decides, and its id is stored
# on the rating so the committee can see exactly why a level came out.
DERIVATION_RULES = [
    ("R0", "No indicator carries verified evidence."),
    ("R1", "Two or more indicators observed high, and none observed weak."),
    ("R2", "At least one indicator observed weak, and none observed high."),
    ("R3", "Mixed or moderate evidence across indicators."),
]


def derive_level(indicators: list[IndicatorRating]) -> tuple[Level, str]:
    """Roll indicator observations up into one competency level.

    Returns the level and the id of the rule that produced it. The model does
    not get a vote here: given the same indicator ratings this function always
    returns the same answer, which is what makes a score reproducible months
    later from stored evidence.
    """
    rated = [i for i in indicators if i.has_verified_evidence()]
    if not rated:
        return (Level.NO_EVIDENCE, "R0")

    highs = sum(1 for i in rated if i.observed_level is Level.HIGH)
    weaks = sum(1 for i in rated if i.observed_level is Level.WEAK)

    if highs >= 2 and weaks == 0:
        return (Level.HIGH, "R1")
    if weaks >= 1 and highs == 0:
        return (Level.WEAK, "R2")
    return (Level.NORMAL, "R3")


# The shapes the model is allowed to return live with the stage that asks for
# them, in `extract.py` and `rate.py`. This module stays the storage contract,
# which is the part the platform side mirrors as table columns.
