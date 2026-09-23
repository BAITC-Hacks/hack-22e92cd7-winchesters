"""ATOLA coverage and the water checklist (task LED-08).

The client's interview model asks five things about any experience: what you did
(Action), why you chose that approach (Thinking), what came of it (Outcome), what
you took from it (Learnings), and where you applied that lesson again
(Application). Their weak anchors describe exactly what an answer looks like when
those are missing: "no concrete situations, general phrases", "hard to describe a
real result or their own contribution".

So "water" here is not a tone to detect and it is not deception. It is a list of
components that are absent, each of which is checkable and each of which has a
question attached, because the client's own probe questions are those five
components in interrogative form.

Nothing in this module produces a score, a probability, or a verdict about
honesty. Attempts to detect deception from language do not work: in a controlled
test both open- and closed-vocabulary methods failed to predict deceptive
impression management, and the authors warned organisations off the approach. A
checklist of what is missing is useful and defensible. A sincerity score is
neither.

A short answer is not water. A candidate who names a situation, what they did
and what happened in three sentences has covered three components; a page of
reflection on qualities has covered none.
"""

from __future__ import annotations

from backend.ledger.schema import (
    AtolaComponent,
    AttentionFlag,
    CompetencyRating,
    EvidenceItem,
    EvidenceStatus,
    effective_level,
)

# The order the client presents them in, which is also the order an interviewer
# walks through an answer.
ATOLA_SEQUENCE: tuple[AtolaComponent, ...] = (
    AtolaComponent.ACTION,
    AtolaComponent.THINKING,
    AtolaComponent.OUTCOME,
    AtolaComponent.LEARNINGS,
    AtolaComponent.APPLICATION,
)

# The client's own ATOLA questions, kept close to their wording so an interviewer
# reads something they already recognise rather than a paraphrase of it.
PROBE_FOR_MISSING: dict[AtolaComponent, str] = {
    AtolaComponent.ACTION: "Что конкретно вы сделали? Как вы подошли к этому?",
    AtolaComponent.THINKING: "Можете объяснить своё мышление? Почему выбрали такой подход?",
    AtolaComponent.OUTCOME: "Какой был результат? Как вы его измеряли?",
    AtolaComponent.LEARNINGS: "Что вы поняли, чему научились? Что извлекли из этого опыта?",
    AtolaComponent.APPLICATION: "Приведите пример, когда вы применили эти выводы в другой ситуации.",
}

# What the committee card calls each gap, in the language of the weak anchors.
FLAG_EXPLANATION: dict[AtolaComponent, str] = {
    AtolaComponent.ACTION: (
        "No situated episode: the material describes qualities rather than something "
        "the applicant did in a particular place at a particular time."
    ),
    AtolaComponent.THINKING: "The applicant does not say why they chose the approach they took.",
    AtolaComponent.OUTCOME: "Nothing in the material says what came of it.",
    AtolaComponent.LEARNINGS: "The applicant does not say what they took from the experience.",
    AtolaComponent.APPLICATION: (
        "No second instance: the lesson is stated once and never applied anywhere else."
    ),
}

FLAG_CODE: dict[AtolaComponent, str] = {
    AtolaComponent.ACTION: "no_situated_episode",
    AtolaComponent.THINKING: "no_reasoning",
    AtolaComponent.OUTCOME: "no_outcome_described",
    AtolaComponent.LEARNINGS: "no_learning",
    AtolaComponent.APPLICATION: "no_transfer_example",
}


def _demonstrated(evidence: list[EvidenceItem]) -> list[EvidenceItem]:
    """Evidence that shows behaviour happening, as opposed to asserting it."""
    return [item for item in evidence if item.verified and item.status is EvidenceStatus.PRESENT]


def _asserted(evidence: list[EvidenceItem]) -> list[EvidenceItem]:
    """Evidence that claims a quality with no situation behind it."""
    return [
        item for item in evidence if item.verified and item.status is EvidenceStatus.CLAIMED_ONLY
    ]


def components_present(evidence: list[EvidenceItem]) -> list[AtolaComponent]:
    """Which parts of a behavioural account the demonstrated evidence covers.

    Only demonstrated evidence counts. An applicant who writes "I always deliver
    results" has not described an outcome; they have asserted a disposition, and
    the interview exists to find out which it is.
    """
    covered = {item.atola for item in _demonstrated(evidence)}
    return [component for component in ATOLA_SEQUENCE if component in covered]


def components_missing(evidence: list[EvidenceItem]) -> list[AtolaComponent]:
    """The gaps, in the order an interviewer would walk through them."""
    present = set(components_present(evidence))
    return [component for component in ATOLA_SEQUENCE if component not in present]


def next_probe(evidence: list[EvidenceItem]) -> str:
    """The question that closes the earliest gap in the account.

    Earliest rather than largest: an interviewer who has not established what the
    applicant actually did cannot usefully ask what they learned from it.
    """
    missing = components_missing(evidence)
    return PROBE_FOR_MISSING[missing[0]] if missing else ""


def _dispositional_flag(evidence: list[EvidenceItem]) -> AttentionFlag | None:
    """Raised when everything found is a claim about identity, not about behaviour.

    This is the clearest form of what the client calls water, and it is the one
    worth surfacing on its own: the material is not thin, it is simply all
    assertion.
    """
    asserted = _asserted(evidence)
    if not asserted or _demonstrated(evidence):
        return None
    return AttentionFlag(
        code="dispositional_not_behavioral",
        quote=asserted[0].quote,
        source=asserted[0].source,
        explanation=(
            "Every passage found for this competency asserts a quality rather than "
            "describing an occasion. Worth asking for one concrete instance."
        ),
    )


def _outcome_flag(evidence: list[EvidenceItem]) -> AttentionFlag | None:
    """Raised when a result is claimed but never described in checkable terms."""
    asserted_outcomes = [i for i in _asserted(evidence) if i.atola is AtolaComponent.OUTCOME]
    demonstrated_outcomes = [i for i in _demonstrated(evidence) if i.atola is AtolaComponent.OUTCOME]
    if not asserted_outcomes or demonstrated_outcomes:
        return None
    return AttentionFlag(
        code="outcome_claimed_only",
        quote=asserted_outcomes[0].quote,
        source=asserted_outcomes[0].source,
        explanation=(
            "A result is claimed but not described in a way anyone could check. "
            "Ask how it was measured and what their own contribution was."
        ),
    )


def water_flags(evidence: list[EvidenceItem]) -> list[AttentionFlag]:
    """The checklist for one competency: what is missing, and what to ask.

    Returns an empty list when the account is complete, which is the common case
    for a strong applicant and should look unremarkable on the card. Flags never
    subtract from a level; they are routed to the interviewer as questions.
    """
    if not any(item.verified for item in evidence):
        # Nothing was found at all. That is "no evidence", which the level
        # already says, and repeating it as five separate flags would read as
        # five criticisms of an applicant who simply was not asked.
        return []

    flags = [flag for flag in (_dispositional_flag(evidence), _outcome_flag(evidence)) if flag]
    flags += [
        AttentionFlag(
            code=FLAG_CODE[component],
            explanation=f"{FLAG_EXPLANATION[component]} Suggested probe: {PROBE_FOR_MISSING[component]}",
        )
        for component in components_missing(evidence)
    ]
    return flags


# ── Derived fields ─────────────────────────────────────────────────


def hydrate(rating: CompetencyRating) -> CompetencyRating:
    """Fill the fields that are computed rather than stored.

    `atola_present` and `capped_reason` are both functions of the evidence rows
    and the observed levels, so the database does not carry columns for them.
    Storing a derived value invites the stored copy and the rule that produced
    it to drift apart, and a committee card that shows a cap without the rule
    still agreeing is worse than one that shows nothing.

    The loader that reads a ledger back out of the database calls this once per
    competency, and the values come out identical to the ones the pipeline
    produced. `tests/test_ledger_atola.py` pins that.
    """
    for indicator in rating.indicators:
        indicator.capped_reason = effective_level(indicator)[1]
    evidence = [item for indicator in rating.indicators for item in indicator.evidence]
    rating.atola_present = components_present(evidence)
    return rating
