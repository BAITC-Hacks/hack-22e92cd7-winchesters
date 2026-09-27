"use client";

import { useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import type { ModelCard } from "@/lib/types";
import { useAuth } from "@/lib/useAuth";

export default function ModelCardPage() {
  const { ready } = useAuth({ requireAuth: true, roles: ["committee", "admin"] });
  const [card, setCard] = useState<ModelCard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ready) return;
    api.fairness.modelCard().then(setCard).catch((cause) => {
      setError(cause instanceof ApiError && cause.status === 403 ? "This model card is for committee and admin only." : cause.message);
    });
  }, [ready]);

  if (!ready) return <main className="p-8 text-sm text-ink-2">Checking access...</main>;
  if (error) return <main className="p-8 text-sm text-danger">{error}</main>;
  if (!card) return <main className="p-8 text-sm text-ink-2">Loading model card...</main>;

  return (
    <main className="min-h-screen bg-subtle px-5 py-8 text-ink sm:px-10">
      <div className="mx-auto max-w-6xl">
        <header className="border-b-2 border-ink pb-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ink-2">FAIR-10 / governance</p>
          <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div><h1 className="text-3xl font-semibold tracking-tight">{card.title}</h1><p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-2">A versioned record of intended use, historical holdout evidence, abstention, and oversight.</p></div>
            <span className="w-fit border border-accent-strong bg-accent-soft px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-accent-ink">{card.status.replace("_", " ")}</span>
          </div>
        </header>

        <section className="mt-6 grid gap-6 lg:grid-cols-2">
          <Panel title="Intended use"><p className="text-sm leading-relaxed">{card.intended_use}</p><h3 className="mt-5 text-xs font-semibold uppercase tracking-wider">Out of scope</h3><List items={card.out_of_scope_use} /></Panel>
          <Panel title="Version and data hashes"><dl className="space-y-3 text-xs"><Hash label="Model" value={card.provenance.model_hash} /><Hash label="Prompt" value={card.provenance.prompt_hash} /><Hash label="Rubric" value={card.provenance.rubric_hash} /><Hash label="Evaluation data" value={card.provenance.evaluation_data_hash} /><Hash label="Registration" value={card.provenance.registration_id} /></dl></Panel>
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-2">
          <Panel title="FAIR-12 held-out provenance"><div className="grid grid-cols-2 gap-3"><Stat label="Effective mode" value={card.provenance.execution.effective_mode} /><Stat label="Fallback" value={card.provenance.execution.fallback_used ? "used" : "none"} /><Stat label="Holdout applicants" value={String(card.provenance.split.holdout_applicants)} /><Stat label="Holdout sealed" value={card.provenance.split.holdout_sealed ? "yes" : "no"} /></div><p className="mt-4 text-xs leading-relaxed text-ink-2">Tuning source: {card.provenance.split.tuning_source}. Historical numbers are reported once the scorer and analysis plan are frozen.</p></Panel>
          <Panel title="Production invariance"><div className="grid gap-2 text-sm"><Invariant label="Production score path" changed={card.production_invariance.score_path_changed} /><Invariant label="Ranking" changed={card.production_invariance.ranking_changed} /><Invariant label="Recommendations" changed={card.production_invariance.recommendation_changed} /></div><p className="mt-4 text-xs leading-relaxed text-ink-2">Held-out evaluation is diagnostic only and cannot write candidate scores or decisions.</p></Panel>
        </section>

        <section className="mt-6 border border-line bg-white p-5"><h2 className="text-sm font-semibold uppercase tracking-wider">Current holdout metrics</h2><div className="mt-4 overflow-x-auto"><table className="w-full min-w-[680px] text-left text-sm"><thead className="border-b border-[#eee] text-xs uppercase tracking-wider text-ink-3"><tr><th className="py-2">Competency</th><th>n</th><th>QWK</th><th>ICC</th><th>Human-human ceiling</th><th>Calibration cells</th></tr></thead><tbody>{card.metrics.agreement.map((metric) => <tr key={metric.competency} className="border-b border-line-soft"><td className="py-3">{metric.competency}</td><td className="font-mono">{metric.n}</td><td className="font-mono">{metric.qwk.toFixed(2)}</td><td className="font-mono">{metric.icc?.toFixed(2) ?? "n/a"}</td><td className="font-mono">{metric.human_human_ceiling.qwk?.toFixed(2) ?? "n/a"} / {metric.human_human_ceiling.icc?.toFixed(2) ?? "n/a"}</td><td className="font-mono">{Object.values(metric.calibration).reduce((sum, row) => sum + Object.values(row).reduce((a, value) => a + value, 0), 0)}</td></tr>)}</tbody></table></div></section>

        <section className="mt-6 grid gap-6 lg:grid-cols-2"><Panel title="Abstention and no evidence"><p className="text-sm leading-relaxed">{card.abstention.policy}</p><div className="mt-4 grid grid-cols-2 gap-3"><Stat label="Failed model runs" value={String(card.abstention.failed_model_runs)} /><Stat label="State" value={card.abstention.no_evidence_state.replace("_", " ")} /></div><p className="mt-4 text-xs leading-relaxed text-ink-2">{card.abstention.production_effect}</p></Panel><Panel title="Screening safety"><Stat label={`Admitted in ${card.screening_safety.lowest_band} band`} value={String(card.screening_safety.admitted_in_lowest_band)} /><p className="mt-4 text-sm">Result: <strong>{card.screening_safety.status}</strong>. This is a safety diagnostic, not an automatic cutoff.</p></Panel></section>

        <section className="mt-6 border border-line bg-white p-5"><h2 className="text-sm font-semibold uppercase tracking-wider">Impact ratios and confidence intervals</h2><div className="mt-4 overflow-x-auto"><table className="w-full min-w-[720px] text-left text-sm"><thead className="border-b border-[#eee] text-xs uppercase tracking-wider text-ink-3"><tr><th className="py-2">Dimension</th><th>Group</th><th>n</th><th>Ratio</th><th>95% CI</th><th>State</th></tr></thead><tbody>{card.metrics.impact_ratios.flatMap((dimension) => dimension.groups.map((group) => <tr key={`${dimension.dimension}-${group.group}`} className="border-b border-line-soft"><td className="py-3">{dimension.dimension}</td><td>{group.group}{group.group === dimension.reference_group ? " (reference)" : ""}</td><td className="font-mono">{group.n}</td><td className="font-mono">{group.impact_ratio?.toFixed(2) ?? "n/a"}</td><td className="font-mono">{group.ci_low == null ? "n/a" : `${group.ci_low.toFixed(2)} - ${group.ci_high?.toFixed(2)}`}</td><td>{group.state.replace("_", " ")}</td></tr>))}</tbody></table></div><p className="mt-3 text-xs leading-relaxed text-ink-2">Groups below n=10 or 2% remain visible but are marked not enough data and are not used for conclusions.</p></section>

        <section className="mt-6 border border-[#e4c56a] bg-[#fff9e6] p-5"><h2 className="text-sm font-semibold uppercase tracking-wider text-warn-ink">Known limitations</h2><List items={card.limitations} tone="text-warn-ink" /></section>
        <section className="mt-6 border border-line bg-white p-5"><h2 className="text-sm font-semibold uppercase tracking-wider">Impact assessment · {card.impact_assessment.legal_basis}</h2><p className="mt-3 text-sm leading-relaxed">{card.impact_assessment.scope}</p><p className="mt-3 text-sm leading-relaxed"><strong>Affected people:</strong> {card.impact_assessment.affected_people}</p><div className="mt-5 grid gap-5 md:grid-cols-3"><div><h3 className="text-xs font-semibold uppercase tracking-wider">Risks</h3><List items={card.impact_assessment.risks} /></div><div><h3 className="text-xs font-semibold uppercase tracking-wider">Mitigations</h3><List items={card.impact_assessment.mitigations} /></div><div><h3 className="text-xs font-semibold uppercase tracking-wider">Oversight and monitoring</h3><p className="mt-2 text-sm leading-relaxed">{card.impact_assessment.human_oversight}</p><p className="mt-2 text-sm leading-relaxed">{card.impact_assessment.monitoring}</p></div></div><p className="mt-5 border-t border-[#eee] pt-4 text-xs leading-relaxed text-ink-2"><strong>Residual risk:</strong> {card.impact_assessment.residual_risk}</p></section>
      </div>
    </main>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) { return <section className="border border-line bg-white p-5"><h2 className="text-sm font-semibold uppercase tracking-wider">{title}</h2><div className="mt-4">{children}</div></section>; }
function List({ items, tone = "text-ink-2" }: { items: string[]; tone?: string }) { return <ul className={`mt-3 list-disc space-y-1 pl-5 text-sm leading-relaxed ${tone}`}>{items.map((item) => <li key={item}>{item}</li>)}</ul>; }
function Hash({ label, value }: { label: string; value: string }) { return <div><dt className="text-ink-3">{label}</dt><dd className="break-all font-mono text-ink">{value}</dd></div>; }
function Stat({ label, value }: { label: string; value: string }) { return <div className="border border-[#eee] bg-subtle p-3"><p className="text-xs uppercase tracking-wider text-ink-3">{label}</p><p className="mt-1 font-mono text-xl">{value}</p></div>; }
function Invariant({ label, changed }: { label: string; changed: boolean }) { return <div className="flex items-center justify-between border-b border-[#eee] py-2"><span>{label}</span><strong className={changed ? "text-danger" : "text-accent-ink"}>{changed ? "changed" : "unchanged"}</strong></div>; }