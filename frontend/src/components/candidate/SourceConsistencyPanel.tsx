import type { AIDetectionResult } from "@/lib/types";
import { DarkPanel, Section } from "../ui/Section";

/**
 * What `/api/analysis/ai-detection` returns since LED-02: descriptive facts about
 * the text and checks an interviewer can do in person. There is no authorship
 * verdict. The response still carries `authenticity_score` for compatibility,
 * always 100, and it is deliberately not rendered.
 */
export function SourceConsistencyPanel({
  result,
  loading,
  onRun,
}: {
  result: AIDetectionResult | null;
  loading: boolean;
  onRun: () => void;
}) {
  return (
    <Section title="Source Consistency">
      {result ? (
        <DarkPanel className="text-base space-y-3">
          <p className="text-gray-300">{result.explanation}</p>
          {result.flags.length > 0 && (
            <div>
              <p className="text-sm font-semibold text-gray-400 mb-1">Verify live</p>
              <ul className="space-y-1 text-sm text-gray-200">
                {result.flags.map((f, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="shrink-0 mt-1 w-3 h-3 border border-gray-400 rounded-sm" aria-hidden />
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {result.stylometry && (
            <div className="mt-3 border-t border-[#333] pt-3">
              <p className="text-sm font-semibold text-gray-400 mb-2">Text statistics (descriptive, not a verdict)</p>
              <div className="grid grid-cols-2 gap-x-5 gap-y-2 text-sm">
                {(
                  [
                    ["Vocabulary richness (TTR)", result.stylometry.ttr.toFixed(3)],
                    ["Sentence variance", result.stylometry.sentence_length_variance.toFixed(1)],
                    ["Hapax ratio", result.stylometry.hapax_ratio.toFixed(3)],
                    ["Formality ratio", result.stylometry.formality_ratio.toFixed(3)],
                    ["Avg sentence length", result.stylometry.avg_sentence_length.toFixed(1)],
                    ["Essay-interview overlap", result.stylometry.essay_interview_vocab_overlap.toFixed(3)],
                  ] as const
                ).map(([label, value]) => (
                  <div key={label} className="flex justify-between">
                    <span className="text-gray-400">{label}:</span>
                    <span className="font-mono text-gray-200">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </DarkPanel>
      ) : (
        <button
          className="px-5 py-2.5 bg-[#141414] text-[#c1f11d] rounded-xl text-base font-medium hover:scale-105 transition-transform disabled:opacity-50"
          onClick={onRun}
          disabled={loading}
        >
          {loading ? "Analyzing..." : "Run consistency check"}
        </button>
      )}
    </Section>
  );
}
