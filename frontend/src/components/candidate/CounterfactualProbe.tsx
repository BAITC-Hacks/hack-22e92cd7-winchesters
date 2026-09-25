"use client";

import type { CounterfactualProbeResult, CounterfactualProbeVariant } from "@/lib/types";

interface CounterfactualProbeProps {
  result: CounterfactualProbeResult | null;
  loading: boolean;
  error: string | null;
  onRun: () => void;
}

const markerLabels: Record<string, string> = {
  name: "name / marker",
  region: "region",
  school_type: "school type",
  language: "language",
  speech_style: "speech style",
};

function level(score: number) {
  if (score >= 66.7) return 3;
  if (score >= 33.3) return 2;
  return 1;
}

function Dots({ score }: { score: number }) {
  const active = level(score);
  return (
    <span className="inline-flex items-center gap-1" aria-label={`${active} of 3 competency levels`}>
      {[1, 2, 3].map((dot) => (
        <span
          key={dot}
          className={`h-2.5 w-2.5 rounded-full border ${dot <= active ? "border-[#141414] bg-[#c1f11d]" : "border-[#b8b8b8] bg-white"}`}
        />
      ))}
    </span>
  );
}

function VariantRow({ variant }: { variant: CounterfactualProbeVariant }) {
  return (
    <div className="border-t border-[#e5e5e5] py-3 first:border-t-0">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-[#141414]">
          {markerLabels[variant.marker] ?? variant.marker}
        </span>
        <span className={`font-mono text-xs ${variant.signed_delta === 0 ? "text-[#5d5d5d]" : "text-[#9b2c2c]"}`}>
          {variant.signed_delta > 0 ? "+" : ""}{variant.signed_delta.toFixed(1)}
        </span>
      </div>
      <div className="mt-2 grid grid-cols-1 gap-1.5 sm:grid-cols-2 lg:grid-cols-5">
        {variant.score.dimensions.map((dimension) => (
          <div key={dimension.dimension} className="flex items-center justify-between gap-2 text-[11px] text-[#5d5d5d]">
            <span className="truncate" title={dimension.dimension}>{dimension.dimension.replaceAll("_", " ")}</span>
            <Dots score={dimension.score} />
          </div>
        ))}
      </div>
      {variant.level_flips.length > 0 && (
        <p className="mt-2 text-xs font-semibold text-[#a32626]">Human review: {variant.level_flips.join(", ")}</p>
      )}
    </div>
  );
}

export function CounterfactualProbe({ result, loading, error, onRun }: CounterfactualProbeProps) {
  return (
    <section className="border border-[#d7d7d7] bg-[#fafafa] p-5" aria-labelledby="counterfactual-probe-title">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 id="counterfactual-probe-title" className="text-sm font-semibold uppercase tracking-wider text-[#141414]">
            Swap and rescore
          </h3>
          <p className="mt-1 max-w-2xl text-xs leading-relaxed text-[#5d5d5d]">
            Committee-only bias probe. One protected marker changes per variant; the candidate score and ranking remain untouched.
          </p>
        </div>
        <button
          type="button"
          onClick={onRun}
          disabled={loading}
          className="shrink-0 border border-[#141414] bg-[#141414] px-3 py-2 text-xs font-semibold text-[#c1f11d] disabled:cursor-wait disabled:opacity-60"
        >
          {loading ? "Running..." : "Run probe"}
        </button>
      </div>

      {error && <p className="mt-3 border border-[#e0aaaa] bg-[#fff4f4] p-3 text-xs text-[#8b1e1e]">{error}</p>}

      {result && (
        <div className="mt-4">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-y border-[#e5e5e5] py-3 text-xs">
            <span className={`font-semibold uppercase ${result.flips_for_human_review.length ? "text-[#a32626]" : "text-[#3d4f00]"}`}>
              {result.flips_for_human_review.length ? "Review required" : "No flips"}
            </span>
            <span className="font-mono text-[#141414]">signed delta {result.signed_delta > 0 ? "+" : ""}{result.signed_delta.toFixed(1)}</span>
            <span className="font-mono text-[#5d5d5d]">tolerance +/-{result.tolerance.toFixed(1)} (2 x SD {result.noise_sd.toFixed(1)})</span>
            <span className="text-[#5d5d5d]">{result.status.replace("_", " ")}</span>
          </div>
          <p className="mt-3 text-xs text-[#5d5d5d]">
            Changed: {result.changed_markers.map((marker) => markerLabels[marker] ?? marker).join(", ")}. Prompt {result.prompt_id}; model {result.model_id}.
          </p>
          <div className="mt-2" aria-label="Counterfactual competency results">
            {result.variants.map((variant) => <VariantRow key={variant.id} variant={variant} />)}
          </div>
          <p className="mt-2 text-[11px] leading-relaxed text-[#969696]">{result.notice}</p>
        </div>
      )}
    </section>
  );
}
