"""AI-generated content detection — statistical stylometry + Claude analysis.

BEFORE (old approach):
    Essay text → single Claude call → "does this feel AI-generated?" → score
    Problem: Claude detecting Claude is unreliable. No quantitative basis.
    The entire detection was vibes-based — Claude just "felt" whether it was AI.

AFTER (new approach):
    Stage 1: Statistical stylometry (no AI, pure math)
        - Compute measurable text features: vocabulary richness, sentence variance,
          word length, formality ratio, hapax legomena, essay-interview vocabulary gap
        - These are reproducible numbers, not opinions
        - AI-generated text has telltale statistical signatures:
          low sentence length variance (unnaturally consistent),
          high formality ratio, low hapax ratio (fewer unique rare words)

    Stage 2: Claude qualitative analysis (informed by Stage 1 metrics)
        - Claude receives the essay + interview + the computed metrics
        - Claude focuses on what statistics can't catch: meaning, voice, emotional depth
        - Its assessment is GROUNDED in the numbers, not free-floating

    Stage 3: Combined score
        - Weighted blend: 40% statistical + 60% Claude qualitative
        - If statistics strongly flag something, it shows even if Claude disagrees
"""

from __future__ import annotations

import re
import statistics
from collections import Counter

from backend import llm, settings
from backend.models import AIDetectionResult, Candidate, StylometryMetrics
from backend.privacy import anonymize_candidate


# ── Language detection ──────────────────────────────────────────────

# Kazakh-specific characters (not shared with Russian)
_KAZAKH_CHARS = set("әғқңөұүһі")
# Russian Cyrillic (shared with Kazakh, but without Kazakh-specific chars it's Russian)
_CYRILLIC_CHARS = set("абвгдежзийклмнопрстуфхцчшщъыьэюя")


def detect_language(text: str) -> str:
    """Detect essay language: 'kazakh', 'russian', or 'english'.

    Simple heuristic based on character frequency — no external libraries needed.
    """
    text_lower = text.lower()
    kazakh_count = sum(1 for c in text_lower if c in _KAZAKH_CHARS)
    cyrillic_count = sum(1 for c in text_lower if c in _CYRILLIC_CHARS)
    latin_count = sum(1 for c in text_lower if c.isascii() and c.isalpha())

    # Kazakh uses Cyrillic + extra chars
    if kazakh_count > 5:
        return "kazakh"
    if cyrillic_count > latin_count:
        return "russian"
    return "english"


# ── Formal/filler phrases typical of AI-generated text ─────────────

AI_FILLER_PHRASES_EN = [
    "in conclusion", "furthermore", "moreover", "in addition",
    "it is worth noting", "this experience taught me",
    "i firmly believe", "in today's world", "it goes without saying",
    "this experience has shown me", "i am passionate about",
    "throughout my journey", "i have always been",
    "this has shaped me into", "i strongly believe",
    "needless to say", "as a result of this experience",
    "this opportunity allowed me to", "i am deeply committed",
]

AI_FILLER_PHRASES_RU = [
    "в заключение", "кроме того", "более того", "помимо этого",
    "стоит отметить", "этот опыт научил меня",
    "я твёрдо убеждён", "я твердо убежден", "в современном мире",
    "этот опыт показал мне", "я увлечён", "я увлечена",
    "на протяжении всего пути", "я всегда был", "я всегда была",
    "это сформировало меня", "я глубоко убеждён", "я глубоко убеждена",
    "само собой разумеется", "в результате этого опыта",
    "эта возможность позволила мне", "я глубоко предан",
]

AI_FILLER_PHRASES_KZ = [
    "қорытындылай келе", "сонымен қатар", "одан басқа",
    "атап өту керек", "бұл тәжірибе маған үйретті",
    "мен нық сенемін", "қазіргі заманда",
    "бұл тәжірибе маған көрсетті", "мен құштармын",
    "бүкіл жолым бойында", "мен әрқашан",
    "бұл мені қалыптастырды", "мен терең сенемін",
]

AI_FILLER_PHRASES = AI_FILLER_PHRASES_EN  # default for backward compat


def _get_filler_phrases(lang: str) -> list[str]:
    if lang == "russian":
        return AI_FILLER_PHRASES_RU
    if lang == "kazakh":
        return AI_FILLER_PHRASES_KZ
    return AI_FILLER_PHRASES_EN


# ── Language-specific stylometry thresholds ─────────────────────────
# Kazakh/Russian texts naturally differ from English in structure:
# - Longer words (agglutinative in Kazakh, inflected in Russian)
# - Different sentence length patterns
# - Different hapax ratios due to morphological richness

THRESHOLDS = {
    "english": {
        "sent_var_low": 15,       # below this = suspicious
        "sent_var_high": 30,      # above this = bonus
        "hapax_low": 0.40,        # below this = suspicious
        "hapax_high": 0.55,       # above this = bonus
        "overlap_low": 0.08,      # below this = suspicious
        "overlap_high": 0.15,     # above this = bonus
    },
    "russian": {
        "sent_var_low": 12,       # Russian sentences are more variable in length
        "sent_var_high": 25,
        "hapax_low": 0.45,        # Russian morphology = more unique word forms
        "hapax_high": 0.60,
        "overlap_low": 0.06,      # Lower overlap expected (more word forms)
        "overlap_high": 0.12,
    },
    "kazakh": {
        "sent_var_low": 10,       # Kazakh agglutination = highly variable word/sent length
        "sent_var_high": 20,
        "hapax_low": 0.50,        # Agglutinative = many unique word forms naturally
        "hapax_high": 0.65,
        "overlap_low": 0.05,
        "overlap_high": 0.10,
    },
}


# ── Stage 1: Statistical stylometry ───────────────────────────────


def compute_stylometry(
    essay_text: str,
    interview_text: str | None = None,
) -> StylometryMetrics:
    """Compute quantitative text features. Pure math, no AI, fully reproducible.

    Automatically detects essay language (English/Russian/Kazakh) and uses
    language-appropriate filler phrase lists.
    """
    words = essay_text.split()
    words_lower = [w.lower().strip(".,!?;:\"'()") for w in words]
    words_lower = [w for w in words_lower if w]

    if len(words_lower) < 10:
        return StylometryMetrics()

    # Type-token ratio (vocabulary richness)
    # AI text tends to have moderate TTR — diverse but not quirky
    unique = set(words_lower)
    ttr = len(unique) / len(words_lower)

    # Sentence length analysis
    # AI text has LOW variance — unnaturally consistent sentence lengths
    sentences = [s.strip() for s in re.split(r'[.!?]+', essay_text) if s.strip()]
    sent_lengths = [len(s.split()) for s in sentences] if sentences else [0]
    avg_sent_len = statistics.mean(sent_lengths) if sent_lengths else 0
    sent_variance = statistics.variance(sent_lengths) if len(sent_lengths) > 1 else 0

    # Average word length
    avg_word_len = statistics.mean(len(w) for w in words_lower) if words_lower else 0

    # Formality ratio: count of AI filler phrases per 100 words
    # Uses language-specific filler phrases
    lang = detect_language(essay_text)
    filler_phrases = _get_filler_phrases(lang)
    text_lower = essay_text.lower()
    filler_count = sum(1 for phrase in filler_phrases if phrase in text_lower)
    formality_ratio = (filler_count / len(words_lower)) * 100

    # Hapax legomena: words that appear exactly once
    # Human writing has MORE hapax (quirky word choices, personal vocabulary)
    # AI writing has FEWER hapax (sticks to common vocabulary patterns)
    word_counts = Counter(words_lower)
    hapax = sum(1 for count in word_counts.values() if count == 1)
    hapax_ratio = hapax / len(unique) if unique else 0

    # Essay-interview vocabulary overlap (Jaccard similarity)
    # If someone writes a sophisticated essay but speaks casually in interview,
    # the overlap will be LOW — a red flag for AI-written essays
    vocab_overlap = 0.0
    if interview_text and len(interview_text.split()) > 20:
        interview_words = set(
            w.lower().strip(".,!?;:\"'()")
            for w in interview_text.split()
        )
        interview_words = {w for w in interview_words if w and len(w) > 3}
        essay_words = {w for w in unique if len(w) > 3}
        intersection = essay_words & interview_words
        union = essay_words | interview_words
        vocab_overlap = len(intersection) / len(union) if union else 0

    return StylometryMetrics(
        ttr=round(ttr, 4),
        avg_sentence_length=round(avg_sent_len, 1),
        sentence_length_variance=round(sent_variance, 1),
        avg_word_length=round(avg_word_len, 2),
        formality_ratio=round(formality_ratio, 3),
        hapax_ratio=round(hapax_ratio, 4),
        essay_interview_vocab_overlap=round(vocab_overlap, 4),
    )


def compute_statistical_score(
    metrics: StylometryMetrics,
    has_interview: bool,
    lang: str = "english",
) -> tuple[float, list[str]]:
    """Convert stylometry metrics into a statistical authenticity score (0-100).

    Returns (score, flags). Higher = more likely human-written.
    Each check adds or subtracts from a base score of 70.

    Uses language-specific thresholds — Kazakh and Russian have different
    natural text characteristics than English (longer words, richer morphology,
    different sentence length patterns).
    """
    score = 70.0
    flags: list[str] = []
    t = THRESHOLDS.get(lang, THRESHOLDS["english"])

    # Sentence length variance: AI text is unnaturally consistent
    if metrics.sentence_length_variance < t["sent_var_low"]:
        penalty = min((t["sent_var_low"] - metrics.sentence_length_variance) * 1.5, 20)
        score -= penalty
        flags.append(
            f"Low sentence length variance ({metrics.sentence_length_variance:.1f}) — "
            f"unnaturally consistent structure"
        )
    elif metrics.sentence_length_variance > t["sent_var_high"]:
        score += 5  # natural variety bonus

    # Formality ratio: too many AI filler phrases
    if metrics.formality_ratio > 1.0:
        penalty = min(metrics.formality_ratio * 8, 20)
        score -= penalty
        flags.append(
            f"High formality ratio ({metrics.formality_ratio:.2f} filler phrases per 100 words)"
        )

    # Hapax ratio: AI uses fewer unique rare words
    # Kazakh/Russian naturally have higher hapax due to rich morphology
    if metrics.hapax_ratio < t["hapax_low"]:
        penalty = min((t["hapax_low"] - metrics.hapax_ratio) * 40, 15)
        score -= penalty
        flags.append(
            f"Low hapax ratio ({metrics.hapax_ratio:.3f}) — fewer unique word choices than expected"
        )
    elif metrics.hapax_ratio > t["hapax_high"]:
        score += 5  # rich personal vocabulary bonus

    # Essay-interview vocabulary gap (only if interview exists)
    if has_interview and metrics.essay_interview_vocab_overlap > 0:
        if metrics.essay_interview_vocab_overlap < t["overlap_low"]:
            penalty = min((t["overlap_low"] - metrics.essay_interview_vocab_overlap) * 200, 20)
            score -= penalty
            flags.append(
                f"Very low essay-interview vocabulary overlap "
                f"({metrics.essay_interview_vocab_overlap:.3f}) — "
                f"writing voice doesn't match speaking voice"
            )
        elif metrics.essay_interview_vocab_overlap > t["overlap_high"]:
            score += 5  # consistent voice bonus

    return max(min(score, 100), 0), flags


# ── Stage 2: Claude qualitative analysis ──────────────────────────

DETECTION_PROMPT = """\
You are an expert in detecting AI-generated text in university application essays.

You will receive:
1. The candidate's essay
2. Their interview transcript (for voice comparison)
3. PRE-COMPUTED STATISTICAL METRICS from the essay

The statistical metrics have already flagged quantitative concerns. Your job is to assess \
what statistics CANNOT catch: meaning, voice, emotional authenticity, personal specificity.

STATISTICAL METRICS:
{metrics_summary}

{essay_document}

{interview_document}

Focus your analysis on:
1. **Personal specificity**: Does the essay mention concrete names, places, dates, events?
2. **Authentic voice**: Does it sound like a real teenager, with natural quirks and personality?
3. **Emotional depth**: When describing emotions, is there genuine feeling or just labeling?
4. **Consistency with interview**: Does the essay voice match how they speak in the interview?
5. **Unique perspective**: Does the essay offer an angle that feels personal, not generic?

IMPORTANT: Good writing is NOT evidence of AI use. Some students genuinely write well.
Only flag AI concerns when MULTIPLE signals converge.

Writing in a second language is NOT evidence of AI use either. Simple vocabulary,
short sentences and grammatical slips are what a strong applicant writing in
Kazakh, Russian or English as an additional language produces. Never treat them
as signals.

Score authenticity from 0 to 100, where 100 means definitely human-written.
Raise a flag only for a concern you can point to in the text; an empty list of
flags is the right answer for most essays.
"""

DETECTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["authenticity_score", "flags", "explanation"],
    "properties": {
        "authenticity_score": {"type": "number"},
        "flags": {"type": "array", "items": {"type": "string"}},
        "explanation": {"type": "string"},
    },
}


def _format_metrics_for_prompt(metrics: StylometryMetrics, stat_flags: list[str], lang: str = "english") -> str:
    """Format stylometry metrics as readable text for Claude."""
    t = THRESHOLDS.get(lang, THRESHOLDS["english"])
    lines = [
        f"  Detected language: {lang}",
        f"  Vocabulary richness (TTR): {metrics.ttr} (human teens: ~0.5-0.7, AI: ~0.4-0.55)",
        f"  Sentence length variance: {metrics.sentence_length_variance} (human {lang}: >{t['sent_var_high']}, AI: <{t['sent_var_low']})",
        f"  Avg word length: {metrics.avg_word_length} chars",
        f"  Formality ratio: {metrics.formality_ratio} filler phrases per 100 words",
        f"  Hapax ratio: {metrics.hapax_ratio} (human {lang}: >{t['hapax_high']}, AI: <{t['hapax_low']})",
        f"  Essay-interview vocab overlap: {metrics.essay_interview_vocab_overlap}",
    ]
    if stat_flags:
        lines.append("  Statistical flags raised:")
        for f in stat_flags:
            lines.append(f"    - {f}")
    else:
        lines.append("  No statistical flags raised.")
    return "\n".join(lines)


def _clamp_score(value: float) -> float:
    """Keep the model's number inside the declared range.

    The schema fixes the shape but cannot express a numeric bound, so the clamp
    lives in code where it is auditable.
    """
    return max(0.0, min(float(value), 100.0))


# ── Stage 3: Combined detection ──────────────────────────────────


async def detect_ai_content(candidate: Candidate) -> AIDetectionResult:
    """Detect AI-generated content using statistical stylometry + Claude analysis.

    Stage 1: Compute statistical metrics (no AI, reproducible)
    Stage 2: Claude qualitative assessment (informed by metrics)
    Stage 3: Weighted combination (40% statistical + 60% qualitative)
    """
    safe = anonymize_candidate(candidate)

    # Detect essay language for threshold calibration
    lang = detect_language(safe.essay.text)

    # Stage 1: Statistical stylometry (language-aware)
    metrics = compute_stylometry(
        safe.essay.text,
        safe.interview_transcript or None,
    )
    stat_score, stat_flags = compute_statistical_score(
        metrics,
        has_interview=bool(safe.interview_transcript),
        lang=lang,
    )

    # Stage 2: Claude qualitative analysis.
    # Kazakh and mixed-language text goes to the strongest model: low-resource
    # languages degrade disproportionately on smaller ones, and a noisy reading
    # here lands on exactly the applicants this product exists to serve.
    metrics_summary = _format_metrics_for_prompt(metrics, stat_flags, lang)

    prompt = DETECTION_PROMPT.format(
        metrics_summary=metrics_summary,
        essay_document=llm.wrap_document(safe.essay.text, "essay", safe.id),
        interview_document=llm.wrap_document(
            safe.interview_transcript, "interview_transcript", safe.id
        ),
    )

    model = settings.MODEL_FOR_LOW_RESOURCE if lang != "english" else settings.MODEL_EXTRACT
    payload = await llm.complete_json(
        prompt=prompt,
        schema=DETECTION_SCHEMA,
        model=model,
    )
    ai_score = _clamp_score(payload["authenticity_score"])
    ai_flags = payload["flags"]
    ai_explanation = payload["explanation"]

    # Stage 3: Weighted combination
    combined_score = stat_score * 0.4 + ai_score * 0.6
    all_flags = stat_flags + ai_flags

    explanation = (
        f"Language detected: {lang}. "
        f"Statistical analysis: {stat_score:.0f}/100. "
        f"AI qualitative analysis: {ai_score:.0f}/100. "
        f"Combined (40/60 weighted): {combined_score:.0f}/100. "
        f"{ai_explanation}"
    )

    return AIDetectionResult(
        authenticity_score=round(max(min(combined_score, 100), 0), 1),
        flags=all_flags,
        explanation=explanation,
        stylometry=metrics,
    )
