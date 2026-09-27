"use client";

import { useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import type { CohortProbeReport, EvaluationReport } from "@/lib/types";

const pct = (value: number) => `${Math.round(value * 100)}%`;

export function EvaluationHarness() {
  const [report, setReport] = useState<EvaluationReport | null>(null);
  const [cohort, setCohort] = useState<CohortProbeReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.fairness.evaluation(), api.fairness.cohortProbe()])
      .then(([evaluationReport, cohortReport]) => { setReport(evaluationReport); setCohort(cohortReport); })
      .catch((cause) => setError(cause instanceof ApiError && cause.status === 403 ? "Evaluation results are for committee and admin only." : String(cause.message ?? cause)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="border border-line bg-subtle p-5 text-sm text-ink-3">Loading evaluation harness...</p>;
  if (error) return <p className="border border-[#e0aaaa] bg-[#fff4f4] p-4 text-sm text-danger">{error}</p>;
  if (!report) return null;

  return (
    <main className="min-h-screen bg-subtle px-5 py-8 text-ink sm:px-10">
      <div className="mx-auto max-w-6xl">
        <header className="border-b-2 border-ink pb-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ink-2">FAIR-05 / evaluation harness v0</p>
          <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h1 className="text-3xl font-semibold tracking-tight">Scorer evaluation</h1>
              <p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-2">A reproducible synthetic check of level stability, marker invariance, injection handling, and language agreement.</p>
            </div>
            <span data-slot="evaluation-source" className="w-fit border border-accent-strong bg-accent-soft px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-accent-ink">{report.status === "live" ? "live" : `${report.status === "cached_demo" ? "Cached demo" : "Fallback"} · deterministic baseline, no model call`}</span>
          </div>
          {report.status !== "live" && (
            <p className="mt-3 text-xs text-ink-2">
              Figures below come from the deterministic baseline scorer on the synthetic fixture{report.fallback_reason ? ` (${report.fallback_reason})` : ""}. They show the harness, not the AI scorer.
            </p>
          )}
        </header>

        <section className="grid gap-px bg-line sm:grid-cols-2 lg:grid-cols-4" aria-label="Evaluation metrics">
          <Metric label="Gold cases" value={String(report.cases)} note="2 BARS x 3 levels x 3 languages x 2 variants" />
          <Metric label="Level flip rate" value={pct(report.level_flip_rate)} note={`${report.level_flip_count} of ${report.probe_count} marker probes`} />
          <Metric label="Repeat consistency" value={pct(report.repeat_consistency)} note={`${report.repeat_count_per_case} scoring calls per case`} />
          <Metric label="Cross-lingual agreement" value={pct(report.cross_lingual_agreement)} note="kk / ru / en" />
        </section>

        {cohort && <section className="mt-6 border border-line bg-white p-5" aria-labelledby="cohort-probe-title">
          <div className="flex flex-wrap items-end justify-between gap-3 border-b border-[#eee] pb-4">
            <div><h2 id="cohort-probe-title" className="text-sm font-semibold uppercase tracking-wider">FAIR-11 cohort probe</h2><p className="mt-1 text-xs text-ink-2">{cohort.sampled_candidates} sampled candidates, reported per marker and competency.</p></div>
            <span className={`border px-3 py-1 text-xs font-semibold uppercase ${cohort.passed ? "border-accent-strong bg-accent-soft text-accent-ink" : "border-[#e0aaaa] bg-[#fff4f4] text-danger"}`}>{cohort.status}: {cohort.passed ? "pass" : "blocked"}</span>
          </div>
          <div className="mt-4 overflow-x-auto"><table className="w-full min-w-[620px] text-left text-xs"><thead className="border-b border-[#eee] uppercase tracking-wider text-ink-3"><tr><th className="py-2">Marker</th><th>Competency</th><th>Robustness</th><th>Result</th></tr></thead><tbody>{cohort.cells.map((cell) => <tr key={`${cell.marker}-${cell.competency}`} className="border-b border-line-soft"><td className="py-2">{cell.marker}</td><td>{cell.competency.replaceAll("_", " ")}</td><td className="font-mono">{Math.round(cell.robustness_rate * 100)}%</td><td className={cell.passed ? "text-accent-ink" : "font-semibold text-[#a32626]"}>{cell.passed ? "PASS" : "BLOCK"}</td></tr>)}</tbody></table></div>
          <p className="mt-3 text-[11px] text-ink-2">Mode: {cohort.mode}. Tolerance +/-{cohort.tolerance.toFixed(1)}; live, cached, and fallback results remain separate. Production score path, ranking, and recommendation are unchanged.</p>
        </section>}

        <section className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="border border-line bg-white p-5">
            <h2 className="text-sm font-semibold uppercase tracking-wider">Harness checks</h2>
            <div className="mt-4 divide-y divide-[#eee] text-sm">
              <Row label="Exact planted level rate" value={pct(report.exact_level_rate)} />
              <Row label="Injection suite" value={report.injection_suite.passed ? "PASS" : "REVIEW"} />
              <Row label="Injected evidence recovered" value={String(report.injection_suite.verified_injected_evidence)} />
              <Row label="Level changes vs clean injection control" value={String(report.injection_suite.level_changes_vs_clean)} />
              <Row label="Noise calibrated tolerance" value={`+/-${report.tolerance.toFixed(1)} (2 x SD ${report.noise_sd.toFixed(1)})`} />
            </div>
            <p className="mt-4 text-xs leading-relaxed text-ink-2">Tolerance follows FAIR-06 semantics. A marker only counts as a flip when its level changes beyond that calibrated noise band.</p>
          </div>
          <div className="border border-line bg-white p-5">
            <h2 className="text-sm font-semibold uppercase tracking-wider">Reproducibility</h2>
            <dl className="mt-4 space-y-2 text-xs">
              <Info label="Fixture" value={report.fixture_version} />
              <Info label="Fixture hash" value={report.fixture_hash} />
              <Info label="Seed" value={String(report.seed)} />
              <Info label="Prompt" value={report.prompt_id} />
              <Info label="Model" value={report.model_id} />
              <Info label="Rubric" value={report.rubric_id} />
            </dl>
          </div>
        </section>

        <section className="mt-6 border border-[#e4c56a] bg-[#fff9e6] p-5">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-warn-ink">Method limits</h2>
          <ul className="mt-3 list-disc space-y-1 pl-5 text-sm leading-relaxed text-warn-ink">
            {report.methodology_limits.map((limit) => <li key={limit}>{limit}</li>)}
          </ul>
        </section>

        <p className="mt-5 text-xs text-ink-2">Production invariance: score path {report.production_invariance.score_path_changed ? "changed" : "unchanged"}; ranking {report.production_invariance.ranking_changed ? "changed" : "unchanged"}; recommendation {report.production_invariance.recommendation_changed ? "changed" : "unchanged"}.</p>
      </div>
    </main>
  );
}

function Metric({ label, value, note }: { label: string; value: string; note: string }) {
  return <div className="bg-white p-5"><p className="text-xs uppercase tracking-wider text-ink-2">{label}</p><p className="mt-2 font-mono text-3xl">{value}</p><p className="mt-2 text-xs text-ink-3">{note}</p></div>;
}

function Row({ label, value }: { label: string; value: string }) {
  return <div className="flex items-center justify-between gap-4 py-3"><span className="text-ink-2">{label}</span><span className="font-mono font-semibold">{value}</span></div>;
}

function Info({ label, value }: { label: string; value: string }) {
  return <div><dt className="text-ink-3">{label}</dt><dd className="break-all font-mono text-ink">{value}</dd></div>;
}
