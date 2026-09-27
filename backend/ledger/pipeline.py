"""Build a candidate's evidence ledger (task LED-04).

    documents -> extract -> verify -> rate (blind) -> derive -> ledger

The verification step between the two model calls is the load-bearing one. The
extractor proposes quotes; this module checks every one against the source text
before anything else sees it. A quote that is not literally present is dropped,
which means a hallucinated quote cannot become evidence, and neither can a line
an applicant embedded in their essay hoping a model would follow it.

The rater is then given the surviving quotes and nothing else. It never receives
the school, the region, the name, the language or the raw documents.

Entry point for the platform side:

    from backend.ledger.pipeline import build_ledger
    ledger = await build_ledger(candidate)

It returns a `CandidateLedger` and touches no database, so it can be called from
a router now and persisted once the tables exist.
"""

from __future__ import annotations

import asyncio
import logging

from backend import llm, settings
from backend.ledger import atola, extract, rate
from backend.ledger.rubric import COMPETENCY_ORDER, RUBRIC, RUBRIC_VERSION, CompetencyRubric
from backend.ledger.schema import (
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
    effective_level,
    locate_quote,
    verify_quote,
)
from backend.models import Candidate
from backend.privacy import anonymize_candidate
from backend.scoring.ai_detector import detect_language

logger = logging.getLogger(__name__)

PROMPT_VERSION = "led-04.0"


# ── Documents in, background out ──────────────────────────────────


def collect_sources(candidate: Candidate) -> dict[Source, str]:
    """The applicant's own words, keyed by where each came from.

    The application form's structured fields are not here on purpose. School
    type, GPA and the rest live in `protected_attributes` and never enter this
    pipeline; see task LED-01 for why.

    The written presentation is the canonical presentation input (INP-01). The
    video transcript is not a source here: it is ASR output, auxiliary quote
    material for the interviewer, and never scored. An applicant without a
    written presentation simply has no evidence from it.
    """
    available = {
        Source.ESSAY: candidate.essay.text,
        Source.WRITTEN_PRESENTATION: candidate.written_presentation,
        Source.INTERVIEW_NOTES: candidate.interview_transcript,
        Source.RECOMMENDATION_LETTER: candidate.recommendation_summary,
    }
    return {source: text for source, text in available.items() if text and text.strip()}


def render_documents(sources: dict[Source, str], applicant_ref: str) -> str:
    """Wrap each source so the model reads it as data, never as instruction."""
    return "\n\n".join(
        llm.wrap_document(text, source.value, applicant_ref) for source, text in sources.items()
    )


def choose_model(sources: dict[Source, str]) -> str:
    """Route Kazakh and mixed-language applications to the strongest model.

    Low-resource languages degrade disproportionately on smaller models, and a
    noisier reading here lands on precisely the applicants this product exists
    to find. Paying more for those files is the cheapest fairness measure
    available.
    """
    joined = " ".join(sources.values())
    return settings.MODEL_EXTRACT if detect_language(joined) == "english" else settings.MODEL_FOR_LOW_RESOURCE


# ── Verification ──────────────────────────────────────────────────


def verify_proposals(proposals: list[dict], sources: dict[Source, str]) -> list[EvidenceItem]:
    """Keep only the quotes that really appear in the source they name.

    Anything that fails is dropped and counted. A high drop rate is a signal
    worth watching in the eval harness: it usually means a prompt regression or
    a model that has started paraphrasing.
    """
    verified: list[EvidenceItem] = []
    for proposal in proposals:
        source = _source_of(proposal)
        text = sources.get(source, "")
        if not verify_quote(proposal["quote"], text):
            logger.info("dropped unverified quote from %s: %.60s", source.value, proposal["quote"])
            continue
        start, end = locate_quote(proposal["quote"], text)
        verified.append(
            EvidenceItem(
                quote=proposal["quote"],
                source=source,
                char_start=start,
                char_end=end,
                atola=_enum_or_default(AtolaComponent, proposal["atola"], AtolaComponent.NONE),
                status=_enum_or_default(EvidenceStatus, proposal["status"], EvidenceStatus.PRESENT),
                verified=True,
                indicator_hint=proposal["indicator_id"],
            )
        )
    return verified


def _source_of(proposal: dict) -> Source:
    try:
        return Source(proposal["source"])
    except ValueError:
        return Source.ESSAY


def _enum_or_default(enum_type, value: str, default):
    try:
        return enum_type(value)
    except ValueError:
        return default


# ── Assembling one competency ─────────────────────────────────────


def _evidence_for_indicator(indicator_id: str, evidence: list[EvidenceItem]) -> list[EvidenceItem]:
    return [item for item in evidence if item.indicator_hint == indicator_id]


def _indicator_ratings(payload: dict, rubric: CompetencyRubric, evidence: list[EvidenceItem]) -> list[IndicatorRating]:
    """Attach verified quotes to the indicator the rater ruled on.

    Each rating also records whether the level that counts toward the competency
    was capped below the observed one, so the card can say why rather than
    silently showing a different number than the rater gave.
    """
    rated = {item["indicator_id"]: item for item in payload["indicators"]}
    ratings = []
    for indicator in rubric.indicators:
        entry = rated.get(indicator.id, {})
        rating = IndicatorRating(
            indicator_id=indicator.id,
            observed_level=_enum_or_default(Level, entry.get("observed_level", ""), Level.NO_EVIDENCE),
            evidence=_evidence_for_indicator(indicator.id, evidence),
            note=entry.get("note", ""),
        )
        rating.capped_reason = effective_level(rating)[1]
        ratings.append(rating)
    return ratings


def _flags(payload: dict) -> list[AttentionFlag]:
    return [
        AttentionFlag(code=f["code"], quote=f["quote"], explanation=f["explanation"])
        for f in payload["flags"]
    ]


def assemble(payload: dict, rubric: CompetencyRubric, evidence: list[EvidenceItem]) -> CompetencyRating:
    """Turn a rating payload into the stored record, deriving the level here.

    A competency the rubric reserves for humans keeps its indicator detail and
    its flags, so the interviewer has something to work from, and carries no
    level at all. The AI does not get a vote on those two blocks.
    """
    indicators = _indicator_ratings(payload, rubric, evidence)
    reserved = not rubric.ai_may_rate

    level, rule = (None, "") if reserved else derive_level(indicators)
    return CompetencyRating(
        competency=rubric.competency,
        indicators=indicators,
        level=level,
        rule_applied=rule,
        reserved_for_humans=reserved,
        contrastive=payload["contrastive"],
        # The rater's suggested probe, then the client's own pre-approved one,
        # then the question that closes the earliest gap in the account.
        probe_question=(
            payload["probe_question"]
            or (rubric.probes[0] if rubric.probes else "")
            or atola.next_probe(evidence)
        ),
        flags=_flags(payload) + atola.water_flags(evidence),
        atola_present=atola.components_present(evidence),
    )


def empty_rating(rubric: CompetencyRubric) -> CompetencyRating:
    """What a competency looks like when nothing could be assessed.

    Used when a stage fails or no document survived verification. It says
    "no evidence", which is honest, rather than a low level, which would not be.
    """
    reserved = not rubric.ai_may_rate
    return CompetencyRating(
        competency=rubric.competency,
        indicators=[IndicatorRating(indicator_id=i.id) for i in rubric.indicators],
        level=None if reserved else Level.NO_EVIDENCE,
        rule_applied="" if reserved else "R0",
        reserved_for_humans=reserved,
        contrastive="No verified evidence was found in the submitted documents.",
        probe_question=rubric.probes[0] if rubric.probes else "",
    )


# ── The pipeline ──────────────────────────────────────────────────


async def build_competency(competency: Competency, documents: str, sources: dict[Source, str]) -> CompetencyRating:
    """Run both stages for one competency and return its stored record."""
    rubric = RUBRIC[competency]
    try:
        proposals = await extract.extract_evidence(documents, rubric, choose_model(sources))
        evidence = verify_proposals(proposals, sources)
        payload = await rate.rate_competency(evidence, rubric)
        return assemble(payload, rubric, evidence)
    except Exception:
        # One competency failing must not cost the committee the other eight,
        # and it must never be recorded as a weak result.
        logger.exception("ledger stage failed for %s", competency.value)
        return empty_rating(rubric)


async def build_ledger(candidate: Candidate) -> CandidateLedger:
    """Build the full evidence ledger for one applicant."""
    safe = anonymize_candidate(candidate)
    sources = collect_sources(safe)

    ledger = CandidateLedger(
        applicant_ref=candidate.id,
        rubric_version=RUBRIC_VERSION,
        model_judge=settings.MODEL_JUDGE,
        model_extract=settings.MODEL_EXTRACT,
        prompt_version=PROMPT_VERSION,
    )
    if not sources:
        ledger.competencies = [empty_rating(RUBRIC[c]) for c in COMPETENCY_ORDER]
        return ledger

    documents = render_documents(sources, candidate.id)
    ledger.competencies = list(
        await asyncio.gather(
            *(build_competency(c, documents, sources) for c in COMPETENCY_ORDER)
        )
    )
    return ledger
