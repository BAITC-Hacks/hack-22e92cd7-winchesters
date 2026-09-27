import { DIMENSION_LABELS, scoreOf, type Scorer } from "@/lib/dashboard";
import type { RankedCandidate } from "@/lib/types";
import { RecommendationBadge } from "../ui/RecommendationBadge";

export function CandidateCard({
  ranked,
  scorer,
  onSelect,
}: {
  ranked: RankedCandidate;
  scorer: Scorer;
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
      className="bg-white rounded-[16px] border-2 border-line px-4 py-5 cursor-pointer transition-all duration-200 hover:border-accent hover:shadow-[0_0_20px_rgba(193,241,29,0.25)] hover:-translate-y-1"
      onClick={onSelect}
    >
      {/* Header row */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <span className="w-[28px] h-[28px] rounded-[8px] bg-accent text-ink flex items-center justify-center text-xs font-bold shrink-0">
            {ranked.rank}
          </span>
          <h3 className="font-bold text-ink text-base">{c.name}</h3>
        </div>
        {score && <RecommendationBadge score={score} scorer={scorer} tag />}
      </div>

      {/* Score row */}
      {score && (
        <>
          <div className="flex items-baseline gap-2 mb-3">
            {completeness ? (
              <>
                <span className="font-bold text-ink text-xl">{score.overall_score.toFixed(0)}%</span>
                <span className="text-ink-2 text-sm">of the file complete</span>
              </>
            ) : (
              <>
                <span className="font-bold text-ink text-xl">{score.overall_score.toFixed(1)}</span>
                <span className="text-ink-3 text-sm">/ 100</span>
                <span className="ml-1 inline-block px-2 py-0.5 rounded-[6.4px] bg-muted text-ink text-xs font-medium uppercase">AI</span>
              </>
            )}
          </div>

          {/* Dimension bars */}
          <div className="flex flex-col">
            {score.dimensions.map((d, i) => (
              <div
                key={d.dimension}
                className={`flex items-center gap-3 py-2.5 ${i < score.dimensions.length - 1 ? "border-b border-line" : ""}`}
              >
                <span className="w-[72px] shrink-0 text-xs text-ink-3 truncate" title={completeness ? "Section filled in, not a rating" : undefined}>
                  {DIMENSION_LABELS[d.dimension] || d.dimension}
                </span>
                <div className="flex-1 h-2.5 bg-muted rounded-[8px] overflow-hidden">
                  <div
                    className="h-full rounded-[8px] bg-ink-2"
                    style={{ width: `${Math.min((d.score / 100) * 100, 100)}%` }}
                  />
                </div>
                <span className="w-[42px] shrink-0 text-center text-xs font-medium bg-muted text-ink rounded-[8px] py-0.5">
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
