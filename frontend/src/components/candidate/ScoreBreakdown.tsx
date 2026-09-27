import { DEFAULT_WEIGHTS, DIMENSION_LABELS, type Scorer } from "@/lib/dashboard";
import type { CandidateScore } from "@/lib/types";
import { DimensionDetail } from "../ui/DimensionDetail";
import { RecommendationBadge } from "../ui/RecommendationBadge";
import { DarkPanel, Section } from "../ui/Section";

export function ScoreBreakdown({ score, scorer }: { score: CandidateScore; scorer: Scorer }) {
  return (
    <Section title={scorer === "baseline" ? "File Completeness (BASELINE)" : `Score Breakdown (${score.scorer_type.toUpperCase()})`}>
      <div className="flex items-center gap-4 mb-4">
        <span className="text-4xl font-bold text-ink">{score.overall_score.toFixed(1)}</span>
        <RecommendationBadge score={score} scorer={scorer} />
      </div>
      {/* The insight compares dimensions as judgements of the applicant; on the
          baseline they only measure how much material exists, so it is AI-only. */}
      {scorer === "ai" && score.dimensions.length > 0 && <AiInsight score={score} />}
      {score.summary && <p className="text-base text-ink-2 mb-4">{score.summary}</p>}
      <div className="space-y-2">
        {score.dimensions.map((d) => (
          <DimensionDetail key={d.dimension} dim={d} weight={DEFAULT_WEIGHTS[d.dimension] ?? 0} />
        ))}
      </div>
    </Section>
  );
}

function AiInsight({ score }: { score: CandidateScore }) {
  const sorted = [...score.dimensions].sort((a, b) => b.score - a.score);
  const highest = sorted[0];
  const lowest = sorted[sorted.length - 1];
  const highLabel = DIMENSION_LABELS[highest.dimension] || highest.dimension;
  const lowLabel = DIMENSION_LABELS[lowest.dimension] || lowest.dimension;
  const missExplanation =
    lowest.dimension === "growth_trajectory"
      ? "growth potential not captured by transcripts alone"
      : lowest.dimension === "communication"
        ? "communication nuance often lost in paper reviews"
        : `lower ${lowLabel} signal that may improve with holistic review`;
  return (
    <DarkPanel className="mb-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="w-1.5 h-5 bg-accent rounded-full inline-block" />
        <span className="text-sm font-semibold text-accent">AI Insight</span>
      </div>
      <p className="text-sm text-ink-3 leading-relaxed">
        Strong signal in <span className="text-white font-medium">{highLabel}</span> ({highest.score.toFixed(0)}).{" "}
        Traditional screening would miss {missExplanation}.
      </p>
    </DarkPanel>
  );
}
