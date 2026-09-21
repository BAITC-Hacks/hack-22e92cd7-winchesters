"""Stage one: find the quotes. No judgement here (task LED-04).

Extraction is a recall problem. The question is "what in these documents speaks
to this indicator", in three languages, and it is answered well by the cheaper
model. What comes back is a proposal: quotes the model believes are in the
sources. Nothing is trusted until `pipeline.py` has checked each one against the
source text character by character.

Keeping extraction separate from rating buys three things. The rater can be made
blind, because it never receives the raw essay, only verified quotes. The
committee gets the artifact it actually needs, which is quotes rather than
adjectives. And a quote that fails verification can be dropped before it ever
influences a level, which is what stops text smuggled into an essay from
becoming evidence about the applicant.
"""

from __future__ import annotations

import logging

from backend import llm, settings
from backend.ledger.rubric import CompetencyRubric
from backend.ledger.schema import AtolaComponent, EvidenceStatus, Source

logger = logging.getLogger(__name__)

EXTRACTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["evidence"],
    "properties": {
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                # Order matters: the model fills fields in this order, so it
                # commits to a quote and says which indicator it speaks to
                # before it characterises the quote.
                "required": ["quote", "source", "indicator_id", "atola", "status"],
                "properties": {
                    "quote": {"type": "string"},
                    "source": {"type": "string", "enum": [s.value for s in Source]},
                    "indicator_id": {"type": "string"},
                    "atola": {"type": "string", "enum": [a.value for a in AtolaComponent]},
                    "status": {"type": "string", "enum": [s.value for s in EvidenceStatus]},
                },
            },
        }
    },
}


EXTRACTION_SYSTEM = """\
You collect evidence for an admissions committee in Kazakhstan. You do not score \
anyone and you do not form an opinion about any applicant. Your only job is to \
find the places in an applicant's own documents that speak to a named behavioural \
indicator, and to copy them out exactly.

Rules that matter more than completeness:

- Copy quotes CHARACTER FOR CHARACTER from the documents, in whatever language \
they were written. Every quote is checked against the source afterwards, and a \
quote that does not match is discarded. A translated, tidied, summarised or \
partially remembered quote is a discarded quote.
- Returning an empty list is a correct and useful answer. Most applicants will \
have nothing to say about most indicators. An empty list is strictly better than \
a quote that only loosely relates to the indicator.
- Applicants write in Kazakh, in Russian, in English, and frequently mix them \
inside one sentence. This is normal and carries no meaning. Never treat language \
choice, grammar, spelling or vocabulary as evidence of anything.
- You are looking for described behaviour, not for self-description. "I am a \
natural leader" is a claim about identity; mark it `claimed_only`. "I asked each \
of them what they wanted to do first" is behaviour; mark it `present`.

Status values:
- `present`: the quote shows the behaviour happening in a specific situation
- `claimed_only`: the quote asserts the quality but no situation sits behind it
- `contradicted`: the quote argues against the indicator
- `not_assessable`: the source is too garbled to read (a poor transcript, say)
"""


def _indicator_block(rubric: CompetencyRubric) -> str:
    """Render the indicators the extractor is hunting for, with their anchors."""
    lines = [f"Competency: {rubric.label}", f"What it covers: {rubric.description}", "", "Indicators:"]
    for indicator in rubric.indicators:
        lines += [
            f"  id: {indicator.id}",
            f"    what it is: {indicator.label}",
            f"    looks weak when: {indicator.weak}",
            f"    looks normal when: {indicator.normal}",
            f"    looks high when: {indicator.high}",
        ]
    return "\n".join(lines)


def build_prompt(documents: str, rubric: CompetencyRubric) -> str:
    """Documents first, then the target, then the instruction."""
    return f"""\
{documents}

<competency>
{_indicator_block(rubric)}
</competency>

Read the documents above and collect every passage that speaks to one of the
indicators in <competency>. For each passage give the quote exactly as written,
which document it came from, which indicator it speaks to, which part of a
behavioural account it is (action, thinking, outcome, learnings, application, or
none), and its status.

Do not rate anything. Do not decide how good the applicant is. Collect quotes.

If nothing in the documents speaks to any of these indicators, return an empty
list. That is a real answer and it happens often."""


async def extract_evidence(documents: str, rubric: CompetencyRubric, model: str = "") -> list[dict]:
    """Ask for candidate evidence on one competency.

    One competency per call, deliberately. Asking about all nine at once invites
    the model to let a strong impression from one block colour the others, which
    is the halo effect structured interviews exist to prevent.
    """
    payload = await llm.complete_json(
        prompt=build_prompt(documents, rubric),
        schema=EXTRACTION_SCHEMA,
        system=EXTRACTION_SYSTEM,
        model=model or settings.MODEL_EXTRACT,
    )
    proposals = payload["evidence"]
    logger.info(
        "extracted %d proposed quotes for %s", len(proposals), rubric.competency.value
    )
    return proposals
