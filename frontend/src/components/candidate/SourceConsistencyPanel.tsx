import type { AIDetectionResult } from "@/lib/types";

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
    <section className="rounded-2xl border border-line bg-white p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="font-semibold text-ink">Consistency check</h3>
          <p className="mt-1 max-w-xl text-sm text-ink-2">
            Things to verify in person. It never says whether the applicant wrote the text themselves.
          </p>
        </div>
        {!result && (
          <button
            type="button"
            className="shrink-0 rounded-full bg-ink px-4 py-2 text-sm font-semibold text-accent disabled:opacity-50"
            onClick={onRun}
            disabled={loading}
          >
            {loading ? "Analyzing..." : "Run consistency check"}
          </button>
        )}
      </div>
      {result && (
        <div className="mt-4 space-y-3 text-sm">
          <p className="text-ink-2">{result.explanation}</p>
          {result.flags.length > 0 && (
            <ul className="space-y-1.5">
              {result.flags.map((f, i) => (
                <li key={i} className="flex gap-2 text-ink">
                  <span className="mt-1 size-3 shrink-0 rounded-sm border border-ink-3" aria-hidden />
                  {f}
                </li>
              ))}
            </ul>
          )}
          {result.stylometry && (
            <details className="text-xs text-ink-2">
              <summary className="cursor-pointer select-none font-semibold hover:text-ink">Text statistics (descriptive, not a verdict)</summary>
              <div className="mt-2 grid grid-cols-1 gap-x-5 gap-y-1 sm:grid-cols-2">
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
                  <div key={label} className="flex justify-between border-b border-line-soft py-1">
                    <span>{label}</span>
                    <span className="font-mono text-ink">{value}</span>
                  </div>
                ))}
              </div>
            </details>
          )}
        </div>
      )}
    </section>
  );
}
