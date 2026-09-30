"""Demo mode: evidence ledgers without a model key.

Until model keys arrive, the two model calls of the pipeline (extract the
quotes, rate them against the BARS anchors) are replaced by a stand-in:

- the 16 seed applicants use rows written once by hand from their own
  documents (`fixtures/demo_ledgers.json`);
- a newly submitted application uses cue phrases in Kazakh, Russian and
  English, one sentence per indicator.

Everything after those two calls is the real pipeline: each quote is checked
character by character against the anonymized source, levels come from
`derive_level`, and the ATOLA checklist and probes from `atola.py`. Every
ledger built here carries a `demo-` model label, so each view shows it as
demo mode (`provenance.py`), and a cached model run always replaces it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from backend.ledger.pipeline import assemble, collect_sources, verify_proposals
from backend.ledger.provenance import DEMO_PREFIX
from backend.ledger.rubric import COMPETENCY_ORDER, RUBRIC, RUBRIC_VERSION, CompetencyRubric
from backend.ledger.schema import CandidateLedger, Level
from backend.models import Candidate
from backend.privacy import anonymize_candidate

DEMO_AUTHORED = f"{DEMO_PREFIX}authored"
DEMO_RULES = f"{DEMO_PREFIX}rule-based"
DEMO_PROMPT_VERSION = "demo-1"
AUTHORED_FILE = Path(__file__).resolve().parent / "fixtures" / "demo_ledgers.json"

_RANK = {Level.NO_EVIDENCE: 0, Level.WEAK: 1, Level.NORMAL: 2, Level.HIGH: 3}


def load_authored(path: Path | None = None) -> dict[str, list[dict]]:
    """Seed ref -> proposal rows, in the shape the extraction stage returns."""
    raw = json.loads((path or AUTHORED_FILE).read_text(encoding="utf-8"))
    columns = raw["columns"]
    return {ref: [dict(zip(columns, row)) for row in rows] for ref, rows in raw["applicants"].items()}


# ── Rating payload ─────────────────────────────────────────────────


def _observed_levels(rows: list[dict]) -> dict[str, Level]:
    """The strongest level any row gives each indicator."""
    levels: dict[str, Level] = {}
    for row in rows:
        level = Level(row["observed_level"])
        if _RANK[level] > _RANK[levels.get(row["indicator_id"], Level.NO_EVIDENCE)]:
            levels[row["indicator_id"]] = level
    return levels


def _contrastive(rubric: CompetencyRubric, levels: dict[str, Level]) -> str:
    """What would move the level up: the High anchor of the first indicator below it."""
    for indicator in rubric.indicators:
        if levels.get(indicator.id) is not Level.HIGH:
            return f"To move up, evidence of {indicator.label.lower()}: {indicator.high}"
    return "High on every indicator; the interview should confirm it."


def rating_payload(rows: list[dict], rubric: CompetencyRubric) -> dict:
    """The payload the rating stage would return for these rows."""
    levels = _observed_levels(rows)
    return {
        "indicators": [
            {"indicator_id": indicator_id, "note": "", "observed_level": level.value}
            for indicator_id, level in levels.items()
        ],
        "flags": [],
        "contrastive": _contrastive(rubric, levels),
        "probe_question": "",
    }


# ── Rule-based extraction for new applications ─────────────────────

# Stems, matched case-insensitively inside words, so one stem covers the
# inflected forms Kazakh and Russian produce.
_CUES: dict[str, tuple[str, ...]] = {
    "motu.specificity": ("invision", "университет", "university"),
    "motu.informed": ("programme", "program", "curriculum", "mission", "программ", "бағдарлам"),
    "motu.fit": ("want to learn", "хочу научиться", "хочу выучиться", "үйренгім", "үйренуім"),
    "motm.understanding": ("engineer", "technolog", "инженер", "технолог", "технология"),
    "motm.evidence_of_interest": ("taught myself", "on my own", "самостоятельно", "сам ", "өзім"),
    "motm.forward_link": ("i want to", "хочу", "келеді", "plan", "план", "жоспар"),
    "lead.concrete_examples": ("organiz", "организова", "ұйымдастыр", "led ", "руковод", "басқар"),
    "lead.initiative": ("i started", "i created", "i founded", "i launched", "i would start", "я начал", "я создал",
                        "я организовал", "я решил", "начал бы", "начну", "бастадым", "құрдым", "шештім", "бастар едім"),
    "lead.organizing_others": ("team", "volunteer", "split", "divide", "команд", "волонтёр", "волонтер", "распредел",
                               "привлек", "ерікті", "бөлі", "тарт"),
    "lead.responsibility_under_difficulty": ("failed", "mistake", "problem", "неудач", "ошибк", "проблем",
                                             "сәтсіз", "қате", "қиын"),
    "lead.result_and_contribution": ("result", "now ", "won", "в итоге", "теперь", "получилось", "заняли",
                                     "нәтиже", "қазір", "шықты"),
    "team.we_orientation": ("together", "we ", "вместе", "мы ", "бірге", "біз"),
    "team.disagreement": ("disagree", "argu", "conflict", "talk to", "asked", "спор", "конфликт", "поговор",
                          "спросил", "дау", "келіспе", "сөйлес", "сұрад"),
    "team.accountability": ("promise", "responsib", "agreed", "called", "обеща", "ответствен", "договорил",
                            "позвонил", "уәде", "жауапкер", "келістік", "хабарластым", "қоңырау"),
    "val.beyond_self": ("help", "others", "помога", "помощ", "другим", "көмек"),
    "val.ethical_choice": ("honest", "fair", "truth", "refuse", "would not", "wouldn't", "честн", "справедлив",
                           "правд", "отказ", "не стал", "не буду", "адал", "әділ", "шындық", "бас тарт"),
    "val.consistency": ("always", "every week", "всегда", "каждую неделю", "әрқашан", "апта сайын"),
    "prio.reality": ("months", "years", "месяц", "лет", "год", "ай ", "жыл"),
    "prio.ownership": ("i built", "i made", "я сделал", "я собрал", "я построил", "жасадым", "құрастырдым"),
    "prio.consequences": ("people", "students", "families", "люди", "семь", "студент", "адам", "оқушы", "отбасы"),
    "int.explains_complexity": ("explain", "calculat", "объясн", "посчита", "түсіндір", "есепте"),
    "int.transfer": ("again", "also", "another", "снова", "тоже", "другой", "тағы", "басқа"),
    "int.revises": ("changed my", "realized", "learned", "понял", "изменил", "научил", "түсіндім", "өзгерттім", "үйрендім"),
}

_CLAIM = re.compile(
    r"\b(i am|i'm|i always|consider myself|я всегда|я являюсь)\b|считаю себя|мен әрқашан|өзімді|деп санаймын|деп ойлаймын",
    re.IGNORECASE,
)
_ATOLA_CUES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("learnings", ("learned", "realized", "taught me", "понял", "научил", "үйрендім", "түсіндім")),
    ("outcome", ("result", "now ", "became", "в итоге", "теперь", "стал", "нәтиже", "қазір")),
    ("thinking", ("because", "decided", "why", "потому", "решил", "себебі", "өйткені", "шештім")),
    ("application", ("again", "another", "снова", "другой", "тағы", "басқа")),
)
_SENTENCE = re.compile(r"[^.!?\n]+[.!?]?")


# Interview lines put by the interviewer, in the three languages the notes use.
_QUESTION_LINE = re.compile(r"^\s*(Q|С|В)\s*:", re.MULTILINE)


def _sentences(text: str) -> list[str]:
    """The applicant's own sentences: long enough to quote, and not a question."""
    text = "\n".join(line for line in text.splitlines() if not _QUESTION_LINE.match(line))
    return [s.strip() for s in _SENTENCE.findall(text) if len(s.split()) >= 4 and not s.strip().endswith("?")]


def _atola(sentence: str) -> str:
    lowered = sentence.lower()
    found = [component for component, cues in _ATOLA_CUES if any(cue in lowered for cue in cues)]
    return found[0] if found else "action"


def _rule_row(indicator_id: str, sources: dict, competency: str, used: set[str]) -> dict | None:
    """The unused sentence with the most cue hits for one indicator, as a proposal row."""
    cues = _CUES.get(indicator_id, ())
    best, best_hits = None, 0
    for source, text in sources.items():
        for sentence in _sentences(text):
            if sentence in used:
                continue
            hits = sum(cue in sentence.lower() for cue in cues)
            if hits > best_hits:
                best, best_hits = (source, sentence), hits
    if best is None:
        return None
    source, sentence = best
    used.add(sentence)
    claimed = bool(_CLAIM.search(sentence))
    atola = "none" if claimed else _atola(sentence)
    concrete = not claimed and (atola == "outcome" or any(ch.isdigit() for ch in sentence))
    return {
        "competency": competency,
        "indicator_id": indicator_id,
        "observed_level": (Level.HIGH if concrete else Level.NORMAL).value,
        "source": source.value,
        "atola": atola,
        "status": "claimed_only" if claimed else "present",
        "quote": sentence,
    }


def rule_rows(sources: dict, rubric: CompetencyRubric) -> list[dict]:
    """Rule-based proposals for one competency, one sentence per indicator; none for the ones humans rate."""
    if not rubric.ai_may_rate:
        return []
    used: set[str] = set()
    rows = (_rule_row(indicator.id, sources, rubric.competency.value, used) for indicator in rubric.indicators)
    return [row for row in rows if row is not None]


# ── Building the ledger ────────────────────────────────────────────


def build_demo_ledger(candidate: Candidate, authored: list[dict] | None = None) -> CandidateLedger:
    """A ledger from authored rows, or from cue phrases when there are none."""
    sources = collect_sources(anonymize_candidate(candidate))
    label = DEMO_AUTHORED if authored is not None else DEMO_RULES
    ledger = CandidateLedger(
        applicant_ref=candidate.id,
        rubric_version=RUBRIC_VERSION,
        model_judge=label,
        model_extract=label,
        prompt_version=DEMO_PROMPT_VERSION,
    )
    for competency in COMPETENCY_ORDER:
        rubric = RUBRIC[competency]
        if authored is not None:
            rows = [row for row in authored if row["competency"] == competency.value]
        else:
            rows = rule_rows(sources, rubric)
        evidence = verify_proposals(rows, sources)
        ledger.competencies.append(assemble(rating_payload(rows, rubric), rubric, evidence))
    return ledger
