"""ATOLA coverage, the water checklist, and the claimed-only cap (task LED-08).

What these pin: a quote that asserts a quality cannot lift an indicator to high,
missing components become the interviewer's questions rather than a deduction,
a complete account produces no flags at all, and the two derived fields come out
identical whether the pipeline computed them or a loader recomputed them from
stored rows.
"""

from __future__ import annotations

from backend.ledger import atola
from backend.ledger.schema import (
    AtolaComponent,
    CompetencyRating,
    Competency,
    EvidenceItem,
    EvidenceStatus,
    IndicatorRating,
    Level,
    Source,
    derive_level,
    effective_level,
)


def _item(atola_component: AtolaComponent, status=EvidenceStatus.PRESENT, quote="q", verified=True):
    return EvidenceItem(
        quote=quote, source=Source.ESSAY, atola=atola_component, status=status, verified=verified
    )


def _indicator(level: Level, items: list[EvidenceItem], indicator_id="lead.initiative"):
    return IndicatorRating(indicator_id=indicator_id, observed_level=level, evidence=items)


FULL_ACCOUNT = [
    _item(AtolaComponent.ACTION),
    _item(AtolaComponent.THINKING),
    _item(AtolaComponent.OUTCOME),
    _item(AtolaComponent.LEARNINGS),
    _item(AtolaComponent.APPLICATION),
]


# ── Coverage ──────────────────────────────────────────────────────


def test_a_complete_account_covers_every_component():
    assert atola.components_present(FULL_ACCOUNT) == list(atola.ATOLA_SEQUENCE)
    assert atola.components_missing(FULL_ACCOUNT) == []


def test_coverage_is_reported_in_the_order_an_interviewer_walks_it():
    evidence = [_item(AtolaComponent.OUTCOME), _item(AtolaComponent.ACTION)]
    assert atola.components_present(evidence) == [AtolaComponent.ACTION, AtolaComponent.OUTCOME]


def test_an_asserted_quality_does_not_count_as_coverage():
    """"I always deliver results" is not an outcome; it is a claim about identity."""
    asserted = [_item(AtolaComponent.OUTCOME, EvidenceStatus.CLAIMED_ONLY)]
    assert atola.components_present(asserted) == []
    assert AtolaComponent.OUTCOME in atola.components_missing(asserted)


def test_unverified_evidence_never_counts_as_coverage():
    unverified = [_item(AtolaComponent.ACTION, verified=False)]
    assert atola.components_present(unverified) == []


# ── The checklist is questions, not deductions ────────────────────


def test_a_complete_account_raises_no_flags():
    """A strong applicant should look unremarkable, not clean-because-checked."""
    assert atola.water_flags(FULL_ACCOUNT) == []


def test_each_missing_component_becomes_a_flag_carrying_its_probe():
    evidence = [_item(AtolaComponent.ACTION)]
    flags = atola.water_flags(evidence)
    codes = {f.code for f in flags}

    assert "no_outcome_described" in codes
    assert "no_learning" in codes
    assert "no_transfer_example" in codes
    assert "no_situated_episode" not in codes
    for flag in flags:
        assert flag.explanation.strip(), f"{flag.code} has no explanation"


def test_the_probes_are_the_clients_own_atola_questions():
    for component in atola.ATOLA_SEQUENCE:
        assert atola.PROBE_FOR_MISSING[component].strip()
    assert "Что конкретно вы сделали" in atola.PROBE_FOR_MISSING[AtolaComponent.ACTION]
    assert "результат" in atola.PROBE_FOR_MISSING[AtolaComponent.OUTCOME]


def test_the_next_probe_closes_the_earliest_gap():
    """No use asking what they learned before knowing what they did."""
    evidence = [_item(AtolaComponent.LEARNINGS)]
    assert atola.next_probe(evidence) == atola.PROBE_FOR_MISSING[AtolaComponent.ACTION]


def test_a_complete_account_needs_no_probe():
    assert atola.next_probe(FULL_ACCOUNT) == ""


def test_an_all_assertion_account_is_flagged_with_the_applicants_own_words():
    evidence = [
        _item(AtolaComponent.NONE, EvidenceStatus.CLAIMED_ONLY, quote="I am a natural leader"),
    ]
    flags = {f.code: f for f in atola.water_flags(evidence)}
    assert "dispositional_not_behavioral" in flags
    assert flags["dispositional_not_behavioral"].quote == "I am a natural leader"


def test_a_claimed_result_is_flagged_separately_from_a_missing_one():
    evidence = [
        _item(AtolaComponent.ACTION),
        _item(AtolaComponent.OUTCOME, EvidenceStatus.CLAIMED_ONLY, quote="it went really well"),
    ]
    codes = {f.code for f in atola.water_flags(evidence)}
    assert "outcome_claimed_only" in codes


def test_nothing_found_produces_no_flags_at_all():
    """Absence is already said by the level; five flags would read as five criticisms."""
    assert atola.water_flags([]) == []
    assert atola.water_flags([_item(AtolaComponent.ACTION, verified=False)]) == []


# ── The claimed-only cap ──────────────────────────────────────────


def test_an_assertion_alone_cannot_reach_high():
    indicator = _indicator(Level.HIGH, [_item(AtolaComponent.NONE, EvidenceStatus.CLAIMED_ONLY)])
    level, reason = effective_level(indicator)
    assert level is Level.NORMAL
    assert reason


def test_a_demonstrated_quote_can_reach_high():
    indicator = _indicator(Level.HIGH, [_item(AtolaComponent.ACTION)])
    assert effective_level(indicator) == (Level.HIGH, "")


def test_the_cap_does_not_touch_weak_or_normal():
    for level in (Level.WEAK, Level.NORMAL):
        indicator = _indicator(level, [_item(AtolaComponent.NONE, EvidenceStatus.CLAIMED_ONLY)])
        assert effective_level(indicator) == (level, "")


def test_the_cap_reaches_the_competency_level():
    """Two indicators rated high on assertions alone must not make a high block."""
    indicators = [
        _indicator(Level.HIGH, [_item(AtolaComponent.NONE, EvidenceStatus.CLAIMED_ONLY)], "a"),
        _indicator(Level.HIGH, [_item(AtolaComponent.NONE, EvidenceStatus.CLAIMED_ONLY)], "b"),
    ]
    assert derive_level(indicators) == (Level.NORMAL, "R3")


def test_two_demonstrated_highs_still_reach_high():
    indicators = [
        _indicator(Level.HIGH, [_item(AtolaComponent.ACTION)], "a"),
        _indicator(Level.HIGH, [_item(AtolaComponent.OUTCOME)], "b"),
    ]
    assert derive_level(indicators) == (Level.HIGH, "R1")


def test_the_fixture_docstring_claim_is_now_true():
    """The LED-03 fixture said a claimed-only indicator cannot reach high.

    Until this task nothing enforced it, so the comment was a promise the code
    did not keep.
    """
    import json
    import pathlib

    fixture = pathlib.Path(__file__).resolve().parents[1] / "backend" / "ledger" / "fixtures" / "ledger_example.json"
    text = fixture.read_text(encoding="utf-8")
    assert "claimed_only" in text
    claimed = _indicator(Level.HIGH, [_item(AtolaComponent.OUTCOME, EvidenceStatus.CLAIMED_ONLY)])
    assert effective_level(claimed)[0] is not Level.HIGH


# ── Derived fields recompute exactly ──────────────────────────────


def test_hydrate_reproduces_what_the_pipeline_computed():
    """The reason these two fields are not database columns.

    A loader reading stored rows calls `hydrate` and gets the same values the
    pipeline produced, so nothing is lost by declining to persist them.
    """
    indicators = [
        _indicator(Level.HIGH, [_item(AtolaComponent.ACTION)], "a"),
        _indicator(Level.HIGH, [_item(AtolaComponent.OUTCOME, EvidenceStatus.CLAIMED_ONLY)], "b"),
    ]
    computed = CompetencyRating(
        competency=Competency.LEADERSHIP_ABILITIES,
        indicators=indicators,
        atola_present=atola.components_present([i for r in indicators for i in r.evidence]),
    )
    for indicator in computed.indicators:
        indicator.capped_reason = effective_level(indicator)[1]

    # What a loader sees: the stored rows, with the derived fields blank.
    from_storage = CompetencyRating(**{
        **computed.model_dump(),
        "atola_present": [],
        "indicators": [{**i.model_dump(), "capped_reason": ""} for i in computed.indicators],
    })
    atola.hydrate(from_storage)

    assert from_storage.atola_present == computed.atola_present
    assert [i.capped_reason for i in from_storage.indicators] == [
        i.capped_reason for i in computed.indicators
    ]
    assert from_storage.indicators[1].capped_reason, "the cap must survive the round trip"


def test_hydrate_is_idempotent():
    rating = CompetencyRating(
        competency=Competency.TEAMWORK,
        indicators=[_indicator(Level.HIGH, [_item(AtolaComponent.ACTION)], "a")],
    )
    once = atola.hydrate(rating).model_dump()
    twice = atola.hydrate(rating).model_dump()
    assert once == twice
