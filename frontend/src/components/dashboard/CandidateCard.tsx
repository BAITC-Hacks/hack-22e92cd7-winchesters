import { DIMENSION_LABELS, scoreOf, type Scorer } from "@/lib/dashboard";
import type { RankedCandidate } from "@/lib/types";
import { RecommendationBadge } from "../ui/RecommendationBadge";

export function CandidateCard({
  ranked,
  scorer,
  selected = false,
  onSelect,
}: {
  ranked: RankedCandidate;
  scorer: Scorer;
  /** Its details are open in the side panel. */
  selected?: boolean;
  onSelect: () => void;
}) {
  const score = scoreOf(ranked);
  const c = ranked.candidate;
  // The completeness scorer measures how much of the file is filled in, not the
  // applicant: say so, so "Leadership 100" is never read as a leadership rating.
  const completeness = score?.scorer_type !== "ai";

  const missingInterview = !c.interview_transcript || c.interview_transcript.trim() === "";
  const missingRec = !c.recommendation_summary || c.recommendation_summary.trim() === "";
  const missingExtras = c.application.extracurriculars.length === 0;
  const missing = [
    missingInterview && "interview transcript",
    missingRec && "recommendation",
    missingExtras && "extracurriculars",
  ].filter(Boolean) as string[];

  return (
    <div
      role="button"
      tabIndex={0}
      aria-pressed={selected}
      className={`bg-white rounded-[20px] border-2 px-5 py-6 cursor-pointer transition-all duration-200 outline-none hover:border-accent hover:shadow-[0_0_20px_rgba(193,241,29,0.25)] hover:-translate-y-1 focus-visible:border-accent ${
        selected ? "border-accent shadow-[0_0_20px_rgba(193,241,29,0.25)]" : "border-line"
      }`}
      onClick={onSelect}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), onSelect())}
    >
      {/* Header row */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <span className="size-[26px] rounded-[8px] bg-accent text-ink flex items-center justify-center text-[15px] font-semibold shrink-0">
            {ranked.rank}
          </span>
          <h3 className="font-semibold text-ink text-[clamp(16.56px,0.86vw,16.56px)]">{c.name}</h3>
        </div>
        {score && <RecommendationBadge score={score} scorer={scorer} tag />}
      </div>

      {/* Score row */}
      {score && (
        <>
          <div className="flex items-baseline gap-2 mb-3">
            {completeness ? (
              <>
                <span className="font-bold text-ink text-[21px]">{score.overall_score.toFixed(0)}%</span>
                <span className="text-ink-3 text-[15px]">of the file complete</span>
              </>
            ) : (
              <>
                <span className="font-bold text-ink text-[21px]">{score.overall_score.toFixed(1)}</span>
                <span className="text-ink-3 text-[15px]">/ 100</span>
                <span className="ml-1 inline-block px-1.5 py-0.5 rounded-[6px] bg-muted text-ink text-[13px] uppercase">AI</span>
              </>
            )}
          </div>

          {/* Dimension bars */}
          <div className="flex flex-col">
            {score.dimensions.map((d, i) => (
              <div
                key={d.dimension}
                className="flex items-center gap-2 border-b border-line py-2"
              >
                <span className="w-[64px] shrink-0 text-[12px] text-ink-3 truncate" title={completeness ? "Section filled in, not a rating" : undefined}>
                  {DIMENSION_LABELS[d.dimension] || d.dimension}
                </span>
                <div className="flex-1 h-[9px] bg-muted rounded-[10px] overflow-hidden">
                  <div
                    className="h-full rounded-[10px] bg-ink-2"
                    style={{ width: `${Math.min((d.score / 100) * 100, 100)}%` }}
                  />
                </div>
                <span className="w-[44px] shrink-0 text-center text-[14px] bg-accent text-ink rounded-[8px] py-1">
                  {d.score.toFixed(0)}{completeness ? "%" : ""}
                </span>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Missing materials: stated as-is. No weight moves to other sections. */}
      {missing.length > 0 && (
        <div className="mt-3 px-3 py-2 rounded-xl bg-subtle border border-line">
          <span className="text-xs font-semibold text-ink">Incomplete file</span>
          <p className="text-xs text-ink-2 mt-0.5">
            Not submitted: {missing.join(", ")}. Scores use only what is in the file.
          </p>
        </div>
      )}

      {/* Language tags */}
      <div className="mt-4 flex flex-wrap gap-1.5">
        {c.application.languages.map((l) => (
          <span key={l} className="inline-block px-1.5 py-0.5 rounded-[5px] bg-ink text-white text-xs font-medium">
            {l}
          </span>
        ))}
      </div>
    </div>
  );
}
