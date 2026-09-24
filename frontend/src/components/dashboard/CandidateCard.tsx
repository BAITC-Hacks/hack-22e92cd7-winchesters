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

  const missingInterview = !c.interview_transcript || c.interview_transcript.trim() === "";
  const missingRec = !c.recommendation_summary || c.recommendation_summary.trim() === "";
  const missingExtras = c.application.extracurriculars.length === 0;
  const isSparse = missingInterview || missingRec || missingExtras;

  return (
    <div
      className="bg-white rounded-[16px] border-2 border-[#d7d7d7] px-4 py-5 cursor-pointer transition-all duration-200 hover:border-[#c1f11d] hover:shadow-[0_0_20px_rgba(193,241,29,0.25)] hover:-translate-y-1"
      onClick={onSelect}
    >
      {/* Header row */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <span className="w-[28px] h-[28px] rounded-[8px] bg-[#c1f11d] text-[#141414] flex items-center justify-center text-xs font-bold shrink-0">
            {ranked.rank}
          </span>
          <h3 className="font-bold text-[#141414] text-base">{c.name}</h3>
        </div>
        {score && <RecommendationBadge score={score} scorer={scorer} tag />}
      </div>

      {/* Score row */}
      {score && (
        <>
          <div className="flex items-center gap-2 mb-3">
            <span className="font-bold text-[#141414] text-xl">{score.overall_score.toFixed(1)}</span>
            <span className="text-[#969696] text-sm">/</span>
            <span className="text-[#969696] text-sm">100</span>
            <span className="ml-2 inline-block px-2 py-0.5 rounded-[6.4px] bg-[#eae9e9] text-[#141414] text-xs font-medium uppercase">
              {score.scorer_type === "ai" ? "AI" : "COMPLETENESS"}
            </span>
          </div>

          {/* Dimension bars */}
          <div className="flex flex-col">
            {score.dimensions.map((d, i) => (
              <div
                key={d.dimension}
                className={`flex items-center gap-3 py-2.5 ${i < score.dimensions.length - 1 ? "border-b border-[#d7d7d7]" : ""}`}
              >
                <span className="w-[72px] shrink-0 text-xs text-[#969696] truncate">
                  {DIMENSION_LABELS[d.dimension] || d.dimension}
                </span>
                <div className="flex-1 h-2.5 bg-[#eae9e9] rounded-[8px] overflow-hidden">
                  <div
                    className="h-full rounded-[8px] bg-[#5d5d5d]"
                    style={{ width: `${Math.min((d.score / 100) * 100, 100)}%` }}
                  />
                </div>
                <span className="w-[42px] shrink-0 text-center text-xs font-medium bg-[#c1f11d] text-[#141414] rounded-[8px] py-0.5">
                  {d.score.toFixed(0)}
                </span>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Sparse Profile badge */}
      {isSparse && (
        <div className="mt-3 px-3 py-2 rounded-xl bg-amber-50 border border-amber-200">
          <span className="text-xs font-semibold text-amber-700">Sparse Profile</span>
          <p className="text-xs text-amber-600 mt-0.5">Weight shifted to Essay &amp; Teaching Challenge</p>
        </div>
      )}

      {/* Language tags */}
      <div className="mt-4 flex flex-wrap gap-1.5">
        {c.application.languages.map((l) => (
          <span key={l} className="inline-block px-1.5 py-0.5 rounded-[5px] bg-[#141414] text-white text-xs font-medium">
            {l}
          </span>
        ))}
      </div>
    </div>
  );
}
