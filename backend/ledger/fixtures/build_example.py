"""Generate the worked-example ledger both sides build against (task LED-03).

Run from the repo root:  python backend/ledger/fixtures/build_example.py

The example is generated rather than hand-written so it can never drift from
`backend/ledger/schema.py`. It deliberately contains one of every case the
committee card has to render:

- a competency at HIGH, derived from two indicators with verified quotes
- a competency at WEAK
- a competency at NO_EVIDENCE, which must not look like WEAK
- a competency reserved for humans, carrying flags but no level
- an indicator the rater called HIGH on an assertion alone, capped to NORMAL
- a competency whose ATOLA coverage has gaps, with the probe that closes the first
- a Kazakh quote, so nobody assumes the ledger is ASCII
"""

from __future__ import annotations

import json
import pathlib
import sys

# Run as a plain script from anywhere, the way notebooks/validation_analysis.py does.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from backend.ledger import atola  # noqa: E402
from backend.ledger.rubric import RUBRIC_VERSION  # noqa: E402
from backend.ledger.schema import (  # noqa: E402
    AtolaComponent,
    AttentionFlag,
    CandidateLedger,
    Competency,
    CompetencyRating,
    EvidenceItem,
    EvidenceStatus,
    IndicatorRating,
    Level,
    Source,
    derive_level,
)

OUT = pathlib.Path(__file__).resolve().parent / "ledger_example.json"


def _evidence(quote: str, source: Source, atola: AtolaComponent, status: EvidenceStatus) -> EvidenceItem:
    return EvidenceItem(
        quote=quote,
        source=source,
        source_ref="art-0001",
        char_start=0,
        char_end=len(quote),
        atola=atola,
        status=status,
        verified=True,
    )


def _rated(competency: Competency, indicators: list[IndicatorRating], **extra) -> CompetencyRating:
    """Build a rating with its level derived and its computed fields filled."""
    level, rule = derive_level(indicators)
    evidence = [item for indicator in indicators for item in indicator.evidence]
    rating = CompetencyRating(
        competency=competency,
        indicators=indicators,
        level=level,
        rule_applied=rule,
        flags=atola.water_flags(evidence),
        **extra,
    )
    return atola.hydrate(rating)


def build() -> CandidateLedger:
    leadership = _rated(
        Competency.LEADERSHIP_ABILITIES,
        [
            IndicatorRating(
                indicator_id="lead.concrete_examples",
                observed_level=Level.HIGH,
                evidence=[
                    _evidence(
                        "I organised thirty volunteers from three villages with no budget",
                        Source.ESSAY,
                        AtolaComponent.ACTION,
                        EvidenceStatus.PRESENT,
                    )
                ],
                note="Names the scale, the places and their own role.",
            ),
            IndicatorRating(
                indicator_id="lead.initiative",
                observed_level=Level.HIGH,
                evidence=[
                    _evidence(
                        "Ешкім бастамаған соң, мен өзім бастадым",
                        Source.WRITTEN_PRESENTATION,
                        AtolaComponent.ACTION,
                        EvidenceStatus.PRESENT,
                    )
                ],
                note="Started it because nobody else had; quote kept in the applicant's language.",
            ),
            IndicatorRating(
                # The rater read this as high. It is an assertion with no occasion
                # behind it, so the roll-up counts it as normal and says so.
                indicator_id="lead.result_and_contribution",
                observed_level=Level.HIGH,
                evidence=[
                    _evidence(
                        "We helped a lot of families that year",
                        Source.ESSAY,
                        AtolaComponent.OUTCOME,
                        EvidenceStatus.CLAIMED_ONLY,
                    )
                ],
                note="Outcome asserted without a measure.",
            ),
        ],
        contrastive=(
            "Already at high. To keep it there under interview, an example of "
            "distributing tasks or resolving a conflict would confirm lead.organizing_others."
        ),
        probe_question="Как вы измеряли результат?",
    )

    teamwork = _rated(
        Competency.TEAMWORK,
        [
            IndicatorRating(
                indicator_id="team.disagreement",
                observed_level=Level.WEAK,
                evidence=[
                    _evidence(
                        "When people argued I just waited for it to pass",
                        Source.ESSAY,
                        AtolaComponent.ACTION,
                        EvidenceStatus.PRESENT,
                    )
                ],
                note="Describes withdrawing rather than helping the group decide.",
            ),
        ],
        contrastive=(
            "Weak to normal would need one instance of bringing a group back to the "
            "task during a disagreement."
        ),
        probe_question="Расскажите про случай, когда в группе начался спор. Что сделали именно вы?",
    )

    motivation_major = _rated(
        Competency.MOTIVATION_MAJOR,
        [
            IndicatorRating(indicator_id="motm.understanding", observed_level=Level.NO_EVIDENCE),
            IndicatorRating(indicator_id="motm.evidence_of_interest", observed_level=Level.NO_EVIDENCE),
        ],
        contrastive="Nothing in the written materials speaks to the choice of major.",
        probe_question="Что именно люди в этой специальности делают каждый день?",
    )

    wounded = CompetencyRating(
        competency=Competency.WOUNDED_LEADERSHIP,
        indicators=[
            IndicatorRating(
                indicator_id="wound.awareness_of_influence",
                observed_level=Level.NO_EVIDENCE,
                note="Not raised in the written materials; the interviewer asks this live.",
            )
        ],
        level=None,
        rule_applied="",
        reserved_for_humans=True,
        probe_question="Что конкретно изменилось в вашем поведении?",
        flags=[
            AttentionFlag(
                code="verify_live",
                explanation=(
                    "No remote evidence. The methodology owner rates this block from "
                    "the live interview; the AI never assigns it a level."
                ),
            )
        ],
    )

    return CandidateLedger(
        applicant_ref="a-7f3c2e91",
        rubric_version=RUBRIC_VERSION,
        model_judge="claude-opus-5",
        model_extract="claude-sonnet-5",
        prompt_version="led-04.0",
        competencies=[leadership, teamwork, motivation_major, wounded],
    )


def main() -> None:
    ledger = build()
    OUT.write_text(
        json.dumps(ledger.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    levels = {c.competency.value: (c.level.value if c.level else "human-only") for c in ledger.competencies}
    print(f"wrote {OUT.relative_to(pathlib.Path.cwd())}")
    print("levels:", json.dumps(levels, ensure_ascii=False))


if __name__ == "__main__":
    main()
