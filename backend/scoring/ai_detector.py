"""Text signals for the interviewer, with the authorship verdict removed (LED-02).

What this used to do: compute seven stylometric numbers, ask Claude whether an
essay "feels" AI-written, blend the two 40/60, and show the committee an
"authenticity score" out of 100 with flags attached to a named applicant.

Why that had to stop:

- Detectors of machine-written text misclassify writing by people working in an
  additional language at very high rates. Published work puts token-statistics
  detectors near a 100% false-positive rate on non-native academic writing, and
  more than half of one set of TOEFL essays was flagged as machine-written while
  essays by native-speaking schoolchildren were classified correctly. The
  mechanism is that constrained vocabulary and simple sentences look like low
  perplexity.
- No calibration for Kazakh exists at all. There is no benchmark, so any number
  we printed for a Kazakh essay was uncalibrated by construction.
- Both of those land on rural Kazakh-speaking applicants, which is the group the
  university exists to find. A rejection touched by a false authorship flag is
  indefensible, and a flag shown to a human anchors that human even if nobody
  subtracts a point.

What it does instead: report descriptive facts about the text, and turn anything
notable into a check the interviewer can actually perform with the person in
front of them. No verdict, no score, no accusation. Where a real answer is
needed, asking the applicant to talk through their own paragraph settles in
thirty seconds what a detector cannot settle at all.
"""

from __future__ import annotations

import re
import statistics
from collections import Counter
from dataclasses import dataclass, field

from backend.models import AIDetectionResult, Candidate, StylometryMetrics
from backend.privacy import anonymize_candidate

# ── Language detection ──────────────────────────────────────────────

# Kazakh-specific characters (not shared with Russian)
_KAZAKH_CHARS = set("әғқңөұүһі")
# Russian Cyrillic (shared with Kazakh, but without Kazakh-specific chars it's Russian)
_CYRILLIC_CHARS = set("абвгдежзийклмнопрстуфхцчшщъыьэюя")


def detect_language(text: str) -> str:
    """Detect essay language: 'kazakh', 'russian', or 'english'.

    A character-frequency heuristic, and a weak one: it has no "mixed" answer,
    so a mostly-Russian text carrying a few Kazakh names comes back as Kazakh.
    Task INP-04 replaces it with proper language identification that treats
    code-switching as a first-class result. Until then, nothing may gate a score
    on this, which after LED-02 nothing does.
    """
    text_lower = text.lower()
    kazakh_count = sum(1 for c in text_lower if c in _KAZAKH_CHARS)
    cyrillic_count = sum(1 for c in text_lower if c in _CYRILLIC_CHARS)
    latin_count = sum(1 for c in text_lower if c.isascii() and c.isalpha())

    if kazakh_count > 5:
        return "kazakh"
    if cyrillic_count > latin_count:
        return "russian"
    return "english"


# ── Descriptive text statistics ────────────────────────────────────


def compute_stylometry(essay_text: str, interview_text: str | None = None) -> StylometryMetrics:
    """Measure the text. Descriptive only: nothing here may become a score.

    These numbers are kept because they are cheap, reproducible and occasionally
    useful to a human reading a file. They are not comparable across languages:
    Kazakh is agglutinative, so it inflates type-token and hapax ratios for
    reasons of grammar rather than of the writer. Task INP-07 replaces them with
    lemma-level measures and per-language norms.
    """
    words = [w.lower().strip(".,!?;:\"'()") for w in essay_text.split()]
    words = [w for w in words if w]
    if len(words) < 10:
        return StylometryMetrics()

    unique = set(words)
    sentences = [s.strip() for s in re.split(r"[.!?]+", essay_text) if s.strip()]
    sentence_lengths = [len(s.split()) for s in sentences] or [0]
    counts = Counter(words)

    return StylometryMetrics(
        ttr=round(len(unique) / len(words), 4),
        avg_sentence_length=round(statistics.mean(sentence_lengths), 1),
        sentence_length_variance=round(
            statistics.variance(sentence_lengths) if len(sentence_lengths) > 1 else 0, 1
        ),
        avg_word_length=round(statistics.mean(len(w) for w in words), 2),
        formality_ratio=0.0,  # retired with LED-02: it measured register, i.e. dialect
        hapax_ratio=round(sum(1 for c in counts.values() if c == 1) / len(unique), 4),
        essay_interview_vocab_overlap=_vocabulary_overlap(unique, interview_text),
    )


def _vocabulary_overlap(essay_words: set[str], interview_text: str | None) -> float:
    """Jaccard overlap between essay and transcript vocabulary.

    Reported, never scored. For Kazakh it is contaminated twice over: by
    transcription error rates on spontaneous speech, and by suffixes, which
    break exact token matching between a written and a spoken form of the same
    word. Task INP-01 makes the applicant's written presentation the input that
    is assessed, which removes the dependency rather than patching it.
    """
    if not interview_text or len(interview_text.split()) <= 20:
        return 0.0
    spoken = {w.lower().strip(".,!?;:\"'()") for w in interview_text.split()}
    spoken = {w for w in spoken if len(w) > 3}
    written = {w for w in essay_words if len(w) > 3}
    union = written | spoken
    return round(len(written & spoken) / len(union), 4) if union else 0.0


# ── Cross-source consistency, as checks a human can run ────────────

_NUMBER = re.compile(r"\b\d[\d\s]{0,6}\b")


@dataclass
class SourceConsistency:
    """What the written sources say, and what an interviewer might ask about.

    Deliberately holds no score. `checks` are phrased as things to ask, never as
    findings about the applicant, because the only reliable way to resolve a
    question about authorship is to let the person talk about their own work.
    """

    language: str = "english"
    sources_compared: list[str] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)
    stylometry: StylometryMetrics | None = None


def _figures_in(text: str) -> set[str]:
    return {m.group().strip() for m in _NUMBER.finditer(text or "")}


def _compare_figures(essay: str, other: str, label: str) -> list[str]:
    """Numbers that appear in one account of an experience but not the other.

    A discrepancy is a question, not a lie: people round, and a transcript
    mishears digits more often than it mishears words.
    """
    essay_figures, other_figures = _figures_in(essay), _figures_in(other)
    if not essay_figures or not other_figures:
        return []
    only_in_essay = sorted(essay_figures - other_figures)[:3]
    if not only_in_essay:
        return []
    return [
        f"The essay gives figures ({', '.join(only_in_essay)}) that the {label} does not. "
        "Worth asking how they were counted."
    ]


def analyze_source_consistency(candidate: Candidate) -> SourceConsistency:
    """Compare what the applicant wrote across the sources they submitted."""
    safe = anonymize_candidate(candidate)
    essay = safe.essay.text
    spoken = safe.interview_transcript or safe.video_transcript or ""

    result = SourceConsistency(
        language=detect_language(essay),
        stylometry=compute_stylometry(essay, spoken or None),
    )
    result.sources_compared = [
        name for name, text in (("essay", essay), ("spoken account", spoken)) if text.strip()
    ]

    if not spoken.strip():
        result.observations.append(
            "Only one written source was submitted, so nothing can be cross-checked."
        )
        result.checks.append(
            "Ask the applicant to talk through one experience from the essay in their own words."
        )
        return result

    result.checks.extend(_compare_figures(essay, spoken, "spoken account"))
    result.checks.append(
        "Ask the applicant to expand on one paragraph of their essay. Someone describing "
        "their own experience adds detail that is not on the page."
    )
    return result


# ── Backwards-compatible shim ──────────────────────────────────────


async def detect_ai_content(candidate: Candidate) -> AIDetectionResult:
    """Deprecated. Returns the consistency view in the old response shape.

    The endpoint and the response model still carry the name `authenticity_score`
    and the dashboard still renders it. Renaming a field and a panel belongs with
    the committee-card rebuild (task LED-05), so until then this fills the old
    shape with something that cannot be mistaken for a verdict: the score is
    fixed and the text says what happened to the feature.
    """
    view = analyze_source_consistency(candidate)
    return AIDetectionResult(
        # A constant, so no ranking, filter or threshold can key off it. The old
        # value was a blend of a stylometric guess and a model's impression.
        authenticity_score=100.0,
        flags=view.checks,
        explanation=(
            "Authorship scoring was removed. Detectors of machine-written text "
            "misclassify writing by people working in an additional language at "
            "very high rates, and no calibration exists for Kazakh, so the number "
            "this panel used to show was not evidence about the applicant. "
            f"Language detected: {view.language}. "
            f"Sources compared: {', '.join(view.sources_compared) or 'essay only'}. "
            + (" ".join(view.observations))
        ).strip(),
        stylometry=view.stylometry,
    )
