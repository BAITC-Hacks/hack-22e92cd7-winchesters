"""
Validation & Analysis Script for InVision U Candidate Scoring System
=====================================================================

This script demonstrates:
1. Score distributions across all candidates (baseline)
2. Trajectory scoring analysis (growth delta vs snapshot)
3. Baseline dimension breakdown and correlation
4. Edge case analysis (missing data, strong/weak profiles)
5. AI detection stylometry metrics
6. Fairness analysis (school type should not determine overall score)

Run: python -m notebooks.validation_analysis
"""

import json
import os
import sys
import statistics

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import Candidate
from backend.scoring.baseline import compute_baseline_score
from backend.scoring.signal_extractor import extract_signals
from backend.scoring.ai_detector import compute_stylometry, compute_statistical_score, detect_language


def load_candidates() -> list[Candidate]:
    path = os.path.join(os.path.dirname(__file__), "..", "backend", "data", "candidates.json")
    with open(path, encoding="utf-8") as f:
        return [Candidate(**c) for c in json.load(f)]


def print_header(title: str):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def analyze_score_distributions(candidates: list[Candidate]):
    """Section 1: Overall score distributions."""
    print_header("1. SCORE DISTRIBUTIONS (Baseline)")

    scores = []
    dimension_scores: dict[str, list[float]] = {}
    recommendations: dict[str, int] = {"recommend": 0, "consider": 0, "needs attention": 0}

    for c in candidates:
        result = compute_baseline_score(c)
        scores.append(result.overall_score)
        recommendations[result.recommendation] += 1
        for d in result.dimensions:
            dimension_scores.setdefault(d.dimension, []).append(d.score)

    print(f"  Candidates evaluated: {len(candidates)}")
    print(f"  Overall score range:  {min(scores):.1f} — {max(scores):.1f}")
    print(f"  Mean:                 {statistics.mean(scores):.1f}")
    print(f"  Median:               {statistics.median(scores):.1f}")
    print(f"  Std deviation:        {statistics.stdev(scores):.1f}")
    print()
    print("  Recommendation distribution:")
    for rec, count in recommendations.items():
        bar = "#" * (count * 3)
        print(f"    {rec:12s}: {count:3d}  {bar}")

    print()
    print("  Per-dimension statistics:")
    print(f"    {'Dimension':25s} {'Mean':>6s} {'Median':>7s} {'Std':>6s} {'Min':>5s} {'Max':>5s}")
    print(f"    {'-' * 55}")
    for dim, vals in sorted(dimension_scores.items()):
        print(
            f"    {dim:25s} {statistics.mean(vals):6.1f} "
            f"{statistics.median(vals):7.1f} {statistics.stdev(vals):6.1f} "
            f"{min(vals):5.1f} {max(vals):5.1f}"
        )

    return scores, dimension_scores


def analyze_trajectory(candidates: list[Candidate]):
    """Section 2: Trajectory scoring — delta vs snapshot comparison."""
    print_header("2. TRAJECTORY SCORING ANALYSIS (Growth Delta)")

    print("  Comparing 'where you are' vs 'how far you came':\n")
    print(
        f"  {'Name':30s} {'School':15s} {'Start':>6s} {'Current':>8s} "
        f"{'Delta':>6s} {'Growth':>7s} {'Overall':>8s} {'Rec':>10s}"
    )
    print(f"  {'-' * 100}")

    data = []
    for c in candidates:
        signals = extract_signals(c)
        g = signals.growth
        score = compute_baseline_score(c)
        growth_dim = next(d for d in score.dimensions if d.dimension == "growth_trajectory")
        data.append({
            "name": c.name,
            "school": c.application.education.school_type,
            "start": g.starting_level,
            "current": g.current_level,
            "delta": g.delta,
            "growth_score": growth_dim.score,
            "overall": score.overall_score,
            "rec": score.recommendation,
        })
        print(
            f"  {c.name:30s} {c.application.education.school_type:15s} "
            f"{g.starting_level:6.1f} {g.current_level:8.1f} "
            f"+{g.delta:5.1f} {growth_dim.score:7.1f} "
            f"{score.overall_score:8.1f} {score.recommendation:>10s}"
        )

    # Key insight: show that school type alone doesn't determine score
    print()
    print("  Key insight — trajectory scoring in action:")

    # Find best example pairs
    high_delta = max(data, key=lambda x: x["delta"])
    low_delta = min(data, key=lambda x: x["delta"])
    print(f"    Highest growth delta: {high_delta['name']} "
          f"(+{high_delta['delta']:.1f}, {high_delta['school']}) → growth={high_delta['growth_score']:.1f}")
    print(f"    Lowest growth delta:  {low_delta['name']} "
          f"(+{low_delta['delta']:.1f}, {low_delta['school']}) → growth={low_delta['growth_score']:.1f}")

    return data


def analyze_edge_cases(candidates: list[Candidate]):
    """Section 3: Edge case analysis — missing data, extreme profiles."""
    print_header("3. EDGE CASE ANALYSIS")

    print("  Missing data impact:\n")
    print(f"  {'Name':30s} {'Interview?':>10s} {'Rec Letter?':>12s} {'Motivation':>11s} {'Communication':>14s} {'Overall':>8s}")
    print(f"  {'-' * 90}")

    for c in candidates:
        score = compute_baseline_score(c)
        motivation = next(d for d in score.dimensions if d.dimension == "motivation_values")
        communication = next(d for d in score.dimensions if d.dimension == "communication")
        has_interview = "Yes" if c.interview_transcript else "NO"
        has_rec = "Yes" if c.recommendation_summary else "NO"
        print(
            f"  {c.name:30s} {has_interview:>10s} {has_rec:>12s} "
            f"{motivation.score:11.1f} {communication.score:14.1f} {score.overall_score:8.1f}"
        )

    # Identify candidates hurt by missing data
    print()
    missing_interview = [c for c in candidates if not c.interview_transcript]
    missing_rec = [c for c in candidates if not c.recommendation_summary]
    print(f"  Candidates without interview: {len(missing_interview)}/{len(candidates)}")
    print(f"  Candidates without recommendation: {len(missing_rec)}/{len(candidates)}")
    if missing_interview:
        print(f"    → These candidates lose up to 20 pts on motivation + 25 pts on communication")
        print(f"    → Confidence should be marked LOW for subjective dimensions")


def analyze_stylometry(candidates: list[Candidate]):
    """Section 4: AI detection stylometry across all candidates."""
    print_header("4. STYLOMETRY ANALYSIS (AI Detection Metrics)")

    print("  Statistical text features across all candidates:\n")
    print(
        f"  {'Name':30s} {'Words':>6s} {'TTR':>6s} {'Sent Var':>9s} "
        f"{'Hapax':>6s} {'Formal':>7s} {'Overlap':>8s} {'Stat Score':>11s}"
    )
    print(f"  {'-' * 90}")

    metrics_list = []
    for c in candidates:
        m = compute_stylometry(c.essay.text, c.interview_transcript or None)
        lang = detect_language(c.essay.text)
        stat_score, flags = compute_statistical_score(m, has_interview=bool(c.interview_transcript), lang=lang)
        metrics_list.append((c.name, m, stat_score, flags))
        print(
            f"  {c.name:30s} {len(c.essay.text.split()):6d} {m.ttr:6.3f} "
            f"{m.sentence_length_variance:9.1f} {m.hapax_ratio:6.3f} "
            f"{m.formality_ratio:7.3f} {m.essay_interview_vocab_overlap:8.3f} {stat_score:11.0f}"
        )

    # Flag suspicious essays
    print()
    flagged = [(name, score, flags) for name, _, score, flags in metrics_list if flags]
    if flagged:
        print(f"  Flagged essays ({len(flagged)}):")
        for name, score, flags in flagged:
            print(f"    {name}: stat_score={score:.0f}")
            for f in flags:
                print(f"      - {f}")
    else:
        print("  No essays flagged by statistical analysis (all look human-written).")

    # Show baselines for reference
    print()
    ttrs = [m.ttr for _, m, _, _ in metrics_list]
    variances = [m.sentence_length_variance for _, m, _, _ in metrics_list]
    hapax_ratios = [m.hapax_ratio for _, m, _, _ in metrics_list]
    print("  Dataset statistics (for reference):")
    print(f"    TTR range:              {min(ttrs):.3f} — {max(ttrs):.3f} (AI typical: 0.40-0.55, human: 0.50-0.70)")
    print(f"    Sentence variance range: {min(variances):.1f} — {max(variances):.1f} (AI typical: 5-25, human: 30-150)")
    print(f"    Hapax ratio range:       {min(hapax_ratios):.3f} — {max(hapax_ratios):.3f} (AI typical: 0.30-0.45, human: 0.50-0.70)")


def analyze_fairness(candidates: list[Candidate]):
    """Section 5: Fairness — school type should not determine overall outcome."""
    print_header("5. FAIRNESS ANALYSIS")

    school_scores: dict[str, list[float]] = {}
    school_growth: dict[str, list[float]] = {}

    for c in candidates:
        score = compute_baseline_score(c)
        school = c.application.education.school_type
        school_scores.setdefault(school, []).append(score.overall_score)
        growth = next(d for d in score.dimensions if d.dimension == "growth_trajectory")
        school_growth.setdefault(school, []).append(growth.score)

    print("  Overall scores by school type (should NOT show systematic bias):\n")
    print(f"  {'School Type':15s} {'Count':>6s} {'Mean':>6s} {'Median':>7s} {'Std':>6s} {'Range':>12s}")
    print(f"  {'-' * 55}")
    for school, vals in sorted(school_scores.items()):
        print(
            f"  {school:15s} {len(vals):6d} {statistics.mean(vals):6.1f} "
            f"{statistics.median(vals):7.1f} "
            f"{statistics.stdev(vals) if len(vals) > 1 else 0:6.1f} "
            f"{min(vals):5.1f}-{max(vals):.1f}"
        )

    print()
    print("  Growth trajectory scores by school type:")
    print(f"  {'School Type':15s} {'Mean Growth':>12s} {'Mean Overall':>13s}")
    print(f"  {'-' * 42}")
    for school in sorted(school_scores.keys()):
        g_vals = school_growth.get(school, [0])
        o_vals = school_scores[school]
        print(
            f"  {school:15s} {statistics.mean(g_vals):12.1f} {statistics.mean(o_vals):13.1f}"
        )

    print()
    print("  Interpretation:")
    print("    - Growth trajectory scores SHOULD differ by school type (that's the point)")
    print("    - Overall scores should NOT be dominated by school type alone")
    print("    - Private school candidates can still score high via academic + leadership")
    print("    - Public/village candidates get growth bonus, compensating for fewer resources")


def print_summary(candidates: list[Candidate], scores: list[float]):
    """Section 6: Summary and model limitations."""
    print_header("6. SUMMARY & KNOWN LIMITATIONS")

    print(f"  Candidates evaluated: {len(candidates)}")
    print(f"  Scoring method:       Rule-based baseline (5 dimensions, weighted)")
    print(f"  Score range:          {min(scores):.1f} — {max(scores):.1f}")
    print(f"  Mean:                 {statistics.mean(scores):.1f}")
    print()
    print("  Known limitations of the baseline scorer:")
    print("    1. Keyword matching is crude — 'I failed to lead' and 'I lead' both match 'lead'")
    print("    2. School type → starting_level mapping is a rough heuristic")
    print("    3. No semantic understanding — baseline can't read between the lines")
    print("    4. Essay quality measured by length/variance, not actual content quality")
    print("    5. Missing interview/recommendation penalizes candidates who had no access")
    print()
    print("  How the AI scorer (Claude) improves on these:")
    print("    1. Reads essay for meaning, not just keywords")
    print("    2. Assesses authenticity, emotional depth, and personal voice")
    print("    3. Cross-references essay claims with interview responses")
    print("    4. Understands context (e.g., 'small village' implies resource constraints)")
    print("    5. Generates nuanced explanations that reference specific evidence")
    print()
    print("  Robustness considerations:")
    print("    - AI scorer may produce slightly different scores on repeated runs")
    print("    - Statistical stylometry thresholds calibrated on English text (may need")
    print("      adjustment for Kazakh/Russian essays in production)")
    print("    - Committee override ensures human judgment always has final say")


if __name__ == "__main__":
    candidates = load_candidates()
    print("\n  InVision U — Candidate Scoring Validation Report")
    print(f"  Generated from {len(candidates)} synthetic candidate profiles\n")

    scores, dim_scores = analyze_score_distributions(candidates)
    analyze_trajectory(candidates)
    analyze_edge_cases(candidates)
    analyze_stylometry(candidates)
    analyze_fairness(candidates)
    print_summary(candidates, scores)

    print(f"\n{'=' * 70}")
    print("  Validation complete.")
    print(f"{'=' * 70}\n")
