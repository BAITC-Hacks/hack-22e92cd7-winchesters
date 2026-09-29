"""Rate a finished scenario on the rubric, like any other document (INP-04).

Only the applicant's own replies are read; the conversation partner's lines
are the question, not evidence. They become one `scenario` source and go
through the ordinary pipeline for the scenario's one competency: quotes are
checked word for word, levels come from `derive_level`, gaps from the ATOLA
checklist. There is no scenario-specific score to learn or to game.

With a model key the two model stages read the replies; without one the
demo extractor stands in for them, the same one new applications use.
"""

from __future__ import annotations

from backend.ledger import demo, extract, rate
from backend.ledger.pipeline import assemble, render_documents, verify_proposals
from backend.ledger.rubric import RUBRIC
from backend.ledger.schema import CompetencyRating, Competency, Source


def applicant_replies(messages: list[dict]) -> str:
    """What the applicant said, one reply per paragraph."""
    return "\n\n".join(m["content"] for m in messages if m["role"] == "user")


def _sources(messages: list[dict]) -> dict[Source, str]:
    replies = applicant_replies(messages)
    return {Source.SCENARIO: replies} if replies.strip() else {}


async def rate_live(messages: list[dict], competency: Competency, applicant_ref: str, model: str = "") -> CompetencyRating:
    """Both model stages over the replies. Raises on a model failure."""
    rubric = RUBRIC[competency]
    sources = _sources(messages)
    if not sources:
        return assemble(demo.rating_payload([], rubric), rubric, [])
    proposals = await extract.extract_evidence(render_documents(sources, applicant_ref), rubric, model)
    evidence = verify_proposals(proposals, sources)
    payload = await rate.rate_competency(evidence, rubric)
    return assemble(payload, rubric, evidence)


def rate_demo(messages: list[dict], competency: Competency) -> CompetencyRating:
    """The rule-based stand-in, for servers without a model key."""
    rubric = RUBRIC[competency]
    sources = _sources(messages)
    rows = demo.rule_rows(sources, rubric) if sources else []
    return assemble(demo.rating_payload(rows, rubric), rubric, verify_proposals(rows, sources))
