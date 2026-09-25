"use client";

import { useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import type { EvaluationReport } from "@/lib/types";

const pct = (value: number) => `${Math.round(value * 100)}%`;

export function EvaluationHarness() {
  const [report, setReport] = useState<EvaluationReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.fairness.evaluation()
      .then(setReport)
      .catch((cause) => setError(cause instanceof ApiError && cause.status === 403 ? "Evaluation results are for committee and admin only." : String(cause.message ?? cause)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="border border-[#d7d7d7] bg-[#fafafa] p-5 text-sm text-[#969696]">Loading evaluation harness...</p>;
  if (error) return <p className="border border-[#e0aaaa] bg-[#fff4f4] p-4 text-sm text-[#8b1e1e]">{error}</p>;
  if (!report) return null;

  return (
    <main className="min-h-screen bg-[#f7f7f5] px-5 py-8 text-[#141414] sm:px-10">
      <div className="mx-auto max-w-6xl">
        <header className="border-b-2 border-[#141414] pb-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#5d5d5d]">FAIR-05 / evaluation harness v0</p>
          <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h1 className="text-3xl font-semibold tracking-tight">Scorer evaluation</h1>
              <p className="mt-2 max-w-2xl text-sm leading-relaxed text-[#5d5d5d]">A reproducible synthetic check of level stability, marker invariance, injection handling, and language agreement.</p>
            </div>
            <span className="w-fit border border-[#b8d900] bg-[#eff8b7] px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-[#3d4f00]">{report.status.replace("_", " ")}</span>
          </div>
        </header>

        <section className="grid gap-px bg-[#d7d7d7] sm:grid-cols-2 lg:grid-cols-4" aria-label="Evaluation metrics">
          <Metric label="Gold cases" value={String(report.cases)} note="2 BARS x 3 levels x 3 languages x 2 variants" />
          <Metric label="Level flip rate" value={pct(report.level_flip_rate)} note={`${report.level_flip_count} of ${report.probe_count} marker probes`} />
          <Metric label="Repeat consistency" value={pct(report.repeat_consistency)} note={`${report.repeat_count_per_case} scoring calls per case`} />
          <Metric label="Cross-lingual agreement" value={pct(report.cross_lingual_agreement)} note="kk / ru / en" />
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="border border-[#d7d7d7] bg-white p-5">
            <h2 className="text-sm font-semibold uppercase tracking-wider">Harness checks</h2>
            <div className="mt-4 divide-y divide-[#eee] text-sm">
              <Row label="Exact planted level rate" value={pct(report.exact_level_rate)} />
              <Row label="Injection suite" value={report.injection_suite.passed ? "PASS" : "REVIEW"} />
              <Row label="Injected evidence recovered" value={String(report.injection_suite.verified_injected_evidence)} />
              <Row label="Level changes vs clean injection control" value={String(report.injection_suite.level_changes_vs_clean)} />
              <Row label="Noise calibrated tolerance" value={`+/-${report.tolerance.toFixed(1)} (2 x SD ${report.noise_sd.toFixed(1)})`} />
            </div>
            <p className="mt-4 text-xs leading-relaxed text-[#5d5d5d]">Tolerance follows FAIR-06 semantics. A marker only counts as a flip when its level changes beyond that calibrated noise band.</p>
          </div>
          <div className="border border-[#d7d7d7] bg-white p-5">
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
          <h2 className="text-sm font-semibold uppercase tracking-wider text-[#6b4b00]">Method limits</h2>
          <ul className="mt-3 list-disc space-y-1 pl-5 text-sm leading-relaxed text-[#6b4b00]">
            {report.methodology_limits.map((limit) => <li key={limit}>{limit}</li>)}
          </ul>
        </section>

        <p className="mt-5 text-xs text-[#5d5d5d]">Production invariance: score path {report.production_invariance.score_path_changed ? "changed" : "unchanged"}; ranking {report.production_invariance.ranking_changed ? "changed" : "unchanged"}; recommendation {report.production_invariance.recommendation_changed ? "changed" : "unchanged"}.</p>
      </div>
    </main>
  );
}

function Metric({ label, value, note }: { label: string; value: string; note: string }) {
  return <div className="bg-white p-5"><p className="text-xs uppercase tracking-wider text-[#5d5d5d]">{label}</p><p className="mt-2 font-mono text-3xl">{value}</p><p className="mt-2 text-xs text-[#969696]">{note}</p></div>;
}

function Row({ label, value }: { label: string; value: string }) {
  return <div className="flex items-center justify-between gap-4 py-3"><span className="text-[#5d5d5d]">{label}</span><span className="font-mono font-semibold">{value}</span></div>;
}

function Info({ label, value }: { label: string; value: string }) {
  return <div><dt className="text-[#969696]">{label}</dt><dd className="break-all font-mono text-[#141414]">{value}</dd></div>;
}
