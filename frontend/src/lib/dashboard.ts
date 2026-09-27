// Ranking, weighting and grouping for the admissions dashboard. No JSX here.
//
// The two scorers mean different things since LED-01, so they are grouped
// differently. The baseline reports how complete a file is (backend/scoring/
// baseline.py), which says nothing about the applicant, so it gets no
// recommendation and no "hidden gem". The AI scorer returns a recommendation.

import type { CandidateScore, RankedCandidate } from "./types";

export type Scorer = "baseline" | "ai";

export const DIMENSION_KEYS = [
  "academic_strength",
  "leadership_potential",
  "motivation_values",
  "growth_trajectory",
  "communication",
] as const;

export const DIMENSION_LABELS: Record<string, string> = {
  academic_strength: "Academic",
  leadership_potential: "Leadership",
  motivation_values: "Motivation",
  growth_trajectory: "Growth",
  communication: "Communication",
};

export const DEFAULT_WEIGHTS: Record<string, number> = {
  academic_strength: 0.15,
  leadership_potential: 0.25,
  motivation_values: 0.25,
  growth_trajectory: 0.2,
  communication: 0.15,
};

export function scoreOf(r: RankedCandidate): CandidateScore | null {
  return r.baseline_score || r.ai_score;
}

// ── AI recommendations ─────────────────────────────────────────────

export type RecommendationGroup = "recommend" | "consider" | "needs_attention";

export function recommendationGroup(rec: string): RecommendationGroup {
  if (rec === "recommend" || rec === "shortlist") return "recommend";
  if (rec === "consider" || rec === "review") return "consider";
  // handles "needs attention", "decline", or any other value
  return "needs_attention";
}

export const RECOMMENDATION_LABELS: Record<RecommendationGroup, string> = {
  recommend: "Recommend",
  consider: "Consider",
  needs_attention: "Needs Attention",
};

// ── Baseline completeness ──────────────────────────────────────────

export type CompletenessGroup = "complete" | "partial" | "sparse";

/** Same cut points as `_confidence_for` in backend/scoring/baseline.py. */
export function completenessGroup(overall: number): CompletenessGroup {
  if (overall >= 75) return "complete";
  if (overall >= 40) return "partial";
  return "sparse";
}

export const COMPLETENESS_LABELS: Record<CompletenessGroup, string> = {
  complete: "Complete file",
  partial: "Partial file",
  sparse: "Sparse file",
};

// ── Grouping for the stats bar, filters and the legacy audit table ──

export type GroupKey = RecommendationGroup | CompletenessGroup;

export function groupOf(r: RankedCandidate, scorer: Scorer): GroupKey | null {
  const score = scoreOf(r);
  if (!score) return null;
  return scorer === "baseline" ? completenessGroup(score.overall_score) : recommendationGroup(score.recommendation);
}

export function groupsFor(scorer: Scorer): { key: GroupKey; label: string }[] {
  return scorer === "baseline"
    ? (["complete", "partial", "sparse"] as const).map((key) => ({ key, label: `${COMPLETENESS_LABELS[key]}s` }))
    : [
        { key: "recommend", label: "Recommended" },
        { key: "consider", label: "Consider" },
        { key: "needs_attention", label: "Needs Attention" },
      ];
}

export function isHiddenGem(r: RankedCandidate, scorer: Scorer): boolean {
  // A gap between one strong dimension and the total is only meaningful for a
  // judgement of the applicant; on file completeness it would be noise.
  if (scorer !== "ai") return false;
  const score = scoreOf(r);
  if (!score) return false;
  if (score.overall_score >= 65) return false;
  return score.dimensions.some((d) => d.score > 70);
}

// ── Client-side reweighting ────────────────────────────────────────

/** Recompute totals with custom weights and re-rank. Instant, no API call. */
export function reweight(raw: RankedCandidate[], weights: Record<string, number>, scorer: Scorer): RankedCandidate[] {
  const recomputed = raw.map((r) => {
    const score = scoreOf(r);
    if (!score) return r;

    const newOverall = score.dimensions.reduce((sum, d) => sum + d.score * (weights[d.dimension] ?? 0.2), 0);
    const roundedOverall = Math.round(newOverall * 10) / 10;
    const updatedScore: CandidateScore = {
      ...score,
      overall_score: roundedOverall,
      // The baseline's recommendation is a constant from the backend and stays
      // that way; thresholding completeness into "recommend" was the bug.
      recommendation:
        scorer === "ai"
          ? roundedOverall >= 70
            ? "recommend"
            : roundedOverall >= 50
              ? "consider"
              : "needs attention"
          : score.recommendation,
    };

    return {
      ...r,
      baseline_score: r.baseline_score ? updatedScore : null,
      ai_score: r.ai_score ? updatedScore : null,
    };
  });

  recomputed.sort((a, b) => (scoreOf(b)?.overall_score ?? 0) - (scoreOf(a)?.overall_score ?? 0));
  return recomputed.map((r, i) => ({ ...r, rank: i + 1 }));
}
