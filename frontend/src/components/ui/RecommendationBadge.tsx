import {
  COMPLETENESS_LABELS,
  RECOMMENDATION_LABELS,
  completenessGroup,
  recommendationGroup,
  type Scorer,
} from "@/lib/dashboard";
import type { CandidateScore } from "@/lib/types";
import { Badge } from "./Badge";

const TAG_STYLES = {
  recommend: "bg-[#c1f11d] text-[#141414]",
  consider: "bg-[#eae9e9] text-[#141414]",
  needs_attention: "bg-red-100 text-red-700",
  complete: "bg-[#eae9e9] text-[#141414]",
  partial: "bg-[#eae9e9] text-[#141414]",
  sparse: "bg-[#eae9e9] text-[#141414]",
} as const;

/**
 * What a score says about the file, per scorer. The AI scorer recommends; the
 * baseline only reports completeness, so it gets a neutral grey tag and never a
 * recommendation colour. `tag` is the square card style, the default is a pill.
 */
export function RecommendationBadge({
  score,
  scorer,
  tag = false,
}: {
  score: CandidateScore;
  scorer: Scorer;
  tag?: boolean;
}) {
  const group =
    scorer === "baseline" ? completenessGroup(score.overall_score) : recommendationGroup(score.recommendation);
  const label =
    scorer === "baseline"
      ? COMPLETENESS_LABELS[group as keyof typeof COMPLETENESS_LABELS]
      : RECOMMENDATION_LABELS[group as keyof typeof RECOMMENDATION_LABELS];

  if (tag) {
    return (
      <span className={`inline-block px-2.5 py-1 rounded-[10px] text-sm font-medium whitespace-nowrap ${TAG_STYLES[group]}`}>
        {label}
      </span>
    );
  }
  return <Badge label={label} color={group === "recommend" ? "green" : group === "needs_attention" ? "red" : "yellow"} />;
}
