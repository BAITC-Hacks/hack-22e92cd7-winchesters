"""Validation report for the scoring path.

Run:  python -m notebooks.validation_analysis

This is a report generator, so stdout is its interface and it prints rather than
logs. It exists to be read by a person, and to be pasted in front of a committee
that wants to see the bias claim demonstrated rather than asserted.

Section 2 is the important one. It takes each application, changes only a
background marker, and prints how much the score moved. Under the Stage-1
scorer those columns were full of double-digit swings, because school type fed a
starting-advantage table and English keyword banks silently scored Kazakh
essays at zero. They should now all read 0.0, and the test suite fails the build
if they do not.
"""

from __future__ import annotations

import copy
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import Candidate  # noqa: E402
from backend.scoring import protected_attributes as pa  # noqa: E402
from backend.scoring.ai_detector import compute_stylometry, detect_language  # noqa: E402
from backend.scoring.baseline import compute_baseline_score  # noqa: E402
from backend.scoring.signal_extractor import extract_signals  # noqa: E402

SCHOOL_TYPES = ["village", "public", "lyceum", "gymnasium", "private", "international"]

HARDSHIP_TEXT = (
    " I come from a village, my single mother could not afford tutors, and I had "
    "to work part-time despite everything."
)

SAME_STORY = {
    "english": "I started a tutoring club and organised thirty volunteers. I learned to listen.",
    "russian": "Я создал клуб репетиторства и организовал тридцать волонтёров. Я научился слушать.",
    "kazakh": "Мен репетиторлық клуб аштым және отыз еріктіні ұйымдастырдым. Тыңдауды үйрендім.",
}


def load_candidates() -> list[Candidate]:
    path = os.path.join(os.path.dirname(__file__), "..", "backend", "data", "candidates.json")
    with open(path, encoding="utf-8") as handle:
        return [Candidate(**c) for c in json.load(handle)]


def header(title: str) -> None:
    print(f"\n{'=' * 78}\n  {title}\n{'=' * 78}\n")


def _score_of(candidate: Candidate) -> float:
    return compute_baseline_score(candidate).overall_score


def _variant(candidate: Candidate, **changes) -> Candidate:
    """Copy an application with one thing changed."""
    twin = copy.deepcopy(candidate)
    if "school_type" in changes:
        twin.application.education.school_type = changes["school_type"]
    if "gpa" in changes:
        twin.application.education.gpa = changes["gpa"]
    if "essay" in changes:
        twin.essay.text = changes["essay"]
        twin.essay.word_count = len(changes["essay"].split())
    return twin


# ── 1. Evidence completeness ──────────────────────────────────────


def report_completeness(candidates: list[Candidate]) -> None:
    header("1. EVIDENCE COMPLETENESS")
    print("  How much material exists per application. Not a judgement of anyone.\n")

    scores = [_score_of(c) for c in candidates]
    print(f"  Applications: {len(candidates)}")
    print(f"  Range:        {min(scores):.1f} to {max(scores):.1f}")
    print(f"  Mean:         {statistics.mean(scores):.1f}")
    print(f"  Median:       {statistics.median(scores):.1f}\n")

    gaps: dict[str, int] = {}
    for candidate in candidates:
        for missing in extract_signals(candidate).availability.missing():
            gaps[missing] = gaps.get(missing, 0) + 1
    print("  Missing sources across the cohort:")
    for source, count in sorted(gaps.items(), key=lambda kv: -kv[1]):
        print(f"    {source:16s} missing for {count:2d} of {len(candidates)}")


# ── 2. Background invariance: the claim, demonstrated ─────────────


def report_invariance(candidates: list[Candidate]) -> None:
    header("2. BACKGROUND INVARIANCE (the bias-exclusion claim)")
    print("  Each row changes one thing about an application and nothing else.")
    print("  'Spread' is the largest gap between variants. Every value must be 0.0.\n")
    print(f"  {'Applicant':10s} {'school type':>12s} {'GPA':>8s} {'hardship':>10s} {'language':>10s}")
    print(f"  {'-' * 54}")

    worst = 0.0
    for candidate in candidates:
        by_school = [_score_of(_variant(candidate, school_type=s)) for s in SCHOOL_TYPES]
        by_gpa = [_score_of(_variant(candidate, gpa=g)) for g in (2.0, 3.0, 3.5, 4.0)]
        hardship = [
            _score_of(candidate),
            _score_of(_variant(candidate, essay=candidate.essay.text + HARDSHIP_TEXT)),
        ]
        by_language = [_score_of(_variant(candidate, essay=text)) for text in SAME_STORY.values()]

        spreads = [max(v) - min(v) for v in (by_school, by_gpa, hardship, by_language)]
        worst = max(worst, *spreads)
        print(
            f"  {candidate.id:10s} {spreads[0]:12.1f} {spreads[1]:8.1f} "
            f"{spreads[2]:10.1f} {spreads[3]:10.1f}"
        )

    print(f"\n  Largest movement anywhere: {worst:.1f}")
    print("  PASS: background does not move the score." if worst == 0 else "  FAIL: investigate.")


# ── 3. What the committee would group by ──────────────────────────


def report_audit_shape(candidates: list[Candidate]) -> None:
    header("3. AUDIT GROUPING (shape of the fairness table)")
    print("  Grouped by a declared attribute, which is what a bias audit needs.")
    print("  The Stage-1 panel grouped by recommendation category, so it could not")
    print("  detect bias at all. Real impact ratios arrive with task FAIR-07.\n")

    groups: dict[str, list[float]] = {}
    for candidate in candidates:
        attributes = pa.extract(candidate)
        key = attributes.school_type or "unknown"
        groups.setdefault(key, []).append(_score_of(candidate))

    print(f"  {'school type':16s} {'n':>3s} {'mean':>7s} {'min':>7s} {'max':>7s}")
    print(f"  {'-' * 44}")
    for key, values in sorted(groups.items()):
        print(
            f"  {key:16s} {len(values):3d} {statistics.mean(values):7.1f} "
            f"{min(values):7.1f} {max(values):7.1f}"
        )
    print("\n  Note: differences here reflect how complete each file is, not merit,")
    print("  and completeness itself is worth auditing: if one group consistently")
    print("  submits fewer sources, the process is losing them before any scoring.")


# ── 4. Language mix and descriptive text stats ────────────────────


def report_language(candidates: list[Candidate]) -> None:
    header("4. LANGUAGE MIX (descriptive only)")
    print("  Detection is a character heuristic with no 'mixed' answer; task INP-04")
    print("  replaces it. Nothing gates a score on this.\n")

    print(f"  {'Applicant':10s} {'language':10s} {'words':>6s} {'TTR':>7s} {'sent var':>9s}")
    print(f"  {'-' * 46}")
    counts: dict[str, int] = {}
    for candidate in candidates:
        language = detect_language(candidate.essay.text)
        counts[language] = counts.get(language, 0) + 1
        metrics = compute_stylometry(candidate.essay.text, candidate.interview_transcript or None)
        print(
            f"  {candidate.id:10s} {language:10s} {candidate.essay.word_count:6d} "
            f"{metrics.ttr:7.3f} {metrics.sentence_length_variance:9.1f}"
        )
    print("\n  Cohort:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    print("  Type-token and hapax ratios are not comparable across these languages:")
    print("  Kazakh inflates both for reasons of grammar. Task INP-07 fixes that.")


# ── 5. Excluded features ──────────────────────────────────────────


def report_exclusions() -> None:
    header("5. FEATURES EXCLUDED FROM SCORING")
    print("  Rendered from the manifest in backend/scoring/protected_attributes.py,")
    print("  so the list cannot drift from what the code actually enforces.\n")
    for feature, reason in sorted(pa.EXCLUDED_FROM_SCORING.items()):
        print(f"  {feature:22s} {reason}")


def main() -> None:
    candidates = load_candidates()
    report_completeness(candidates)
    report_invariance(candidates)
    report_audit_shape(candidates)
    report_language(candidates)
    report_exclusions()
    print()


if __name__ == "__main__":
    main()
