"""Stage two: rate the indicators, seeing only verified evidence (task LED-04).

This is the blind step, and the blindness is the point. The rater receives a
list of quotes that have already been checked against the source, plus the BARS
anchors for the indicators those quotes were attached to. It does not receive
the essay, the application form, the school, the region, the applicant's name,
or the language the documents were written in. A model cannot weigh a background
it never sees, which is a stronger guarantee than instructing it not to: prompt
level anti-bias instructions have been measured to be fragile once realistic
context is present, and side-by-side comparison of candidates makes dialect bias
worse, so the rater also only ever sees one applicant at a time.

It does not return a competency level either. It rates each indicator against
its anchors and `derive_level` in `schema.py` turns those into the level, by a
rule the committee can read.
"""

from __future__ import annotations

import logging

from backend import llm, settings
from backend.ledger.rubric import CompetencyRubric
from backend.ledger.schema import EvidenceItem, Level

logger = logging.getLogger(__name__)

RATING_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["indicators", "flags", "contrastive", "probe_question"],
    "properties": {
        "indicators": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                # `note` before `observed_level`, so the model states which
                # evidence it is relying on before it commits to a level rather
                # than justifying a level it has already picked.
                "required": ["indicator_id", "note", "observed_level"],
                "properties": {
                    "indicator_id": {"type": "string"},
                    "note": {"type": "string"},
                    "observed_level": {"type": "string", "enum": [l.value for l in Level]},
                },
            },
        },
        "flags": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["code", "quote", "explanation"],
                "properties": {
                    "code": {"type": "string"},
                    "quote": {"type": "string"},
                    "explanation": {"type": "string"},
                },
            },
        },
        "contrastive": {"type": "string"},
        "probe_question": {"type": "string"},
    },
}


RATING_SYSTEM = """\
You are rating one competency for a university admissions committee in Kazakhstan, \
against a behaviourally anchored scale the university owns.

You are shown only verified quotes from one applicant's own documents. You are not \
shown their name, school, region, family circumstances, or which language they \
wrote in, and you must not speculate about any of those in order to adjust a \
rating in either direction.

For each indicator, decide which anchor the evidence actually matches:

- `no_evidence`: nothing in the quotes speaks to this indicator. This is the right \
answer whenever the evidence is silent, and it is not a criticism of the applicant. \
Never rate `weak` to mean "I did not see anything": weak means the evidence shows \
the behaviour going badly, and silence is not that.
- `weak`, `normal`, `high`: the evidence matches that anchor's description.

Judge what the applicant describes doing. Do not reward length, polish, fluency, \
formal vocabulary, or the number of quotes. Three plain sentences describing a real \
situation outrank a page of eloquence about qualities.

Where the evidence includes something a human should look at rather than something \
you should score, raise a flag instead of lowering a rating.
"""


def _anchor_block(rubric: CompetencyRubric) -> str:
    lines = [f"Competency: {rubric.label}", ""]
    for indicator in rubric.indicators:
        lines += [
            f"{indicator.id} — {indicator.label}",
            f"  weak:   {indicator.weak}",
            f"  normal: {indicator.normal}",
            f"  high:   {indicator.high}",
            "",
        ]
    return "\n".join(lines)


def _evidence_block(evidence: list[EvidenceItem]) -> str:
    if not evidence:
        return "<evidence>\n(no verified evidence was found for this competency)\n</evidence>"
    lines = ["<evidence>"]
    for index, item in enumerate(evidence, 1):
        lines += [
            f"[{index}] indicator: {item.indicator_hint or 'unassigned'}",
            f"    source: {item.source.value}, part of account: {item.atola.value}, status: {item.status.value}",
            f"    quote: {item.quote}",
        ]
    lines.append("</evidence>")
    return "\n".join(lines)


def build_prompt(evidence: list[EvidenceItem], rubric: CompetencyRubric) -> str:
    """Evidence first, anchors second, the question last."""
    return f"""\
{_evidence_block(evidence)}

<anchors>
{_anchor_block(rubric)}
</anchors>

Rate every indicator listed in <anchors> against the quotes in <evidence>.

Give a short note for each one naming the evidence you relied on, then the level.
Use `no_evidence` wherever the quotes are silent about that indicator.

Then give:
- `contrastive`: what evidence would be needed to reach the next level up,
  phrased in the words of the anchor itself, so it can be read aloud to an
  interviewer and to the applicant. If everything is already at high, say what
  would confirm it in the interview.
- `probe_question`: one question an interviewer could ask to resolve what the
  written evidence leaves open.
- `flags`: anything a human should verify rather than something you should rate."""


async def rate_competency(
    evidence: list[EvidenceItem],
    rubric: CompetencyRubric,
    model: str = "",
) -> dict:
    """Rate one competency's indicators from verified evidence alone."""
    payload = await llm.complete_json(
        prompt=build_prompt(evidence, rubric),
        schema=RATING_SCHEMA,
        system=RATING_SYSTEM,
        model=model or settings.MODEL_JUDGE,
    )
    logger.info(
        "rated %s from %d verified quotes", rubric.competency.value, len(evidence)
    )
    return payload
