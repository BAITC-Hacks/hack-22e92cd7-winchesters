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
          className={`h-2.5 w-2.5 rounded-full border ${dot <= active ? "border-ink bg-accent" : "border-[#b8b8b8] bg-white"}`}
        />
      ))}
    </span>
  );
}

function VariantRow({ variant }: { variant: CounterfactualProbeVariant }) {
  return (
    <div className="border-t border-line-soft py-3 first:border-t-0">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-ink">
          {markerLabels[variant.marker] ?? variant.marker}
        </span>
        <span className={`font-mono text-xs ${variant.signed_delta === 0 ? "text-ink-2" : "text-[#9b2c2c]"}`}>
          {variant.signed_delta > 0 ? "+" : ""}{variant.signed_delta.toFixed(1)}
        </span>
      </div>
      <div className="mt-2 grid grid-cols-1 gap-1.5 sm:grid-cols-2 lg:grid-cols-5">
        {variant.score.dimensions.map((dimension) => (
          <div key={dimension.dimension} className="flex items-center justify-between gap-2 text-[11px] text-ink-2">
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
  const flips = result?.flips_for_human_review ?? [];
  const swapped = [...new Set(result?.changed_markers.map((marker) => markerLabels[marker] ?? marker) ?? [])];
  return (
    <section className="rounded-2xl border border-line bg-white p-5" aria-labelledby="counterfactual-probe-title">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 id="counterfactual-probe-title" className="font-semibold text-ink">
            Swap and rescore
          </h3>
          <p className="mt-1 max-w-xl text-sm text-ink-2">
            Scores the same application again with the name, region, school, language or speech style changed. If a level
            moves, background is affecting the score.
          </p>
        </div>
        <button
          type="button"
          onClick={onRun}
          disabled={loading}
          className="shrink-0 rounded-full bg-ink px-4 py-2 text-sm font-semibold text-accent disabled:cursor-wait disabled:opacity-60"
        >
          {loading ? "Running..." : "Run probe"}
        </button>
      </div>

      {error && <p className="mt-3 rounded-xl border border-danger/20 bg-danger-soft p-3 text-sm text-danger">{error}</p>}

      {result && (
        <div className="mt-4 space-y-3">
          <p
            className={`rounded-xl px-4 py-3 text-sm font-medium ${flips.length ? "bg-danger-soft text-danger" : "bg-accent-soft text-accent-ink"}`}
          >
            {flips.length
              ? `Review required: a level changed when we swapped ${flips.join(", ")}.`
              : `No level changed when we swapped ${swapped.join(", ")}.`}
          </p>
          {result.status !== "live" && (
            <span data-slot="probe-source" className="inline-block rounded-full bg-subtle px-2.5 py-0.5 text-xs text-ink-2">
              {result.status === "cached_demo" ? "Cached demo" : "Fallback"} · deterministic baseline, no model call
            </span>
          )}
          <details className="text-xs text-ink-2">
            <summary className="cursor-pointer select-none font-semibold hover:text-ink">See each swap</summary>
            <p className="mt-2 font-mono">
              signed delta {result.signed_delta > 0 ? "+" : ""}
              {result.signed_delta.toFixed(1)} · tolerance ±{result.tolerance.toFixed(1)} (2 × SD {result.noise_sd.toFixed(1)}) · prompt{" "}
              {result.prompt_id} · model {result.model_id}
            </p>
            <div className="mt-2" aria-label="Counterfactual competency results">
              {result.variants.map((variant) => (
                <VariantRow key={variant.id} variant={variant} />
              ))}
            </div>
            <p className="mt-2 text-[11px] leading-relaxed text-ink-3">{result.notice}</p>
          </details>
        </div>
      )}
    </section>
  );
}
