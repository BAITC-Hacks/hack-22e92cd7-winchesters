"use client";

import { useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import type { HeldoutReproducibility } from "@/lib/types";
import { useAuth } from "@/lib/useAuth";

export default function ReproducibilityPage() {
  const { ready } = useAuth({ requireAuth: true, roles: ["committee", "admin"] });
  const [result, setResult] = useState<HeldoutReproducibility | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ready) return;
    api.fairness.heldoutReproduce().then(setResult).catch((cause) => {
      setError(cause instanceof ApiError && cause.status === 403 ? "This reproducibility check is for committee and admin only." : cause.message);
    });
  }, [ready]);

  if (!ready) return <main className="p-8 text-sm text-ink-2">Checking access...</main>;
  if (error) return <main className="p-8 text-sm text-danger">{error}</main>;
  if (!result) return <main className="p-8 text-sm text-ink-2">Replaying held-out ratings...</main>;

  const passed = result.byte_identical;
  return (
    <main className="min-h-screen bg-subtle px-5 py-8 text-ink sm:px-10">
      <div className="mx-auto max-w-5xl">
        <header className="border-b-2 border-ink pb-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ink-2">FAIR-13 / governance</p>
          <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div><h1 className="text-3xl font-semibold tracking-tight">Held-out reproducibility</h1><p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-2">Every stored rating is replayed under the frozen prompt, rubric, and data hashes.</p></div>
            <span className={`w-fit border px-3 py-1.5 text-xs font-semibold uppercase tracking-wider ${passed ? "border-accent-strong bg-accent-soft text-accent-ink" : "border-[#d99a9a] bg-[#fff0f0] text-danger"}`}>{result.status}</span>
          </div>
        </header>

        <section className="mt-6 grid gap-6 lg:grid-cols-2">
          <Panel title="Replay result"><div className="grid grid-cols-2 gap-3"><Stat label="Ratings replayed" value={String(result.ratings_recomputed)} /><Stat label="Byte identical" value={result.byte_identical ? "yes" : "no"} /><Stat label="Source mode" value={result.source_provenance.effective_mode} /><Stat label="Fallback" value={result.source_provenance.fallback_used ? "used" : "none"} /></div></Panel>
          <Panel title="Production invariance"><div className="grid gap-2 text-sm"><Invariant label="Score path" changed={result.production_invariance.score_path_changed} /><Invariant label="Ranking" changed={result.production_invariance.ranking_changed} /><Invariant label="Recommendations" changed={result.production_invariance.recommendation_changed} /></div></Panel>
        </section>

        <section className="mt-6 border border-line bg-white p-5"><h2 className="text-sm font-semibold uppercase tracking-wider">Frozen hashes</h2><dl className="mt-4 grid gap-4 text-xs sm:grid-cols-3"><Hash label="Prompt" value={result.frozen_hashes.prompt} /><Hash label="Rubric" value={result.frozen_hashes.rubric} /><Hash label="Data" value={result.frozen_hashes.data} /></dl><div className="mt-5 grid gap-4 border-t border-[#eee] pt-4 text-xs sm:grid-cols-2"><Hash label="Stored report bytes" value={result.expected_hash} /><Hash label="Replayed report bytes" value={result.actual_hash} /></div></section>

        {!passed && <section className="mt-6 border border-[#d99a9a] bg-[#fff0f0] p-5"><h2 className="text-sm font-semibold uppercase tracking-wider text-danger">Mismatch diagnostics</h2><ul className="mt-3 space-y-2 text-sm text-danger">{result.mismatches.map((item) => <li key={item.path}><span className="font-mono">{item.path}</span>: stored {String(item.expected)} / replayed {String(item.actual)}</li>)}</ul></section>}
      </div>
    </main>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) { return <section className="border border-line bg-white p-5"><h2 className="text-sm font-semibold uppercase tracking-wider">{title}</h2><div className="mt-4">{children}</div></section>; }
function Stat({ label, value }: { label: string; value: string }) { return <div className="border border-[#eee] bg-subtle p-3"><p className="text-xs uppercase tracking-wider text-ink-3">{label}</p><p className="mt-1 font-mono text-xl">{value}</p></div>; }
function Hash({ label, value }: { label: string; value: string }) { return <div><dt className="text-ink-3">{label}</dt><dd className="break-all font-mono text-ink">{value}</dd></div>; }
function Invariant({ label, changed }: { label: string; changed: boolean }) { return <div className="flex items-center justify-between border-b border-[#eee] py-2"><span>{label}</span><strong className={changed ? "text-danger" : "text-accent-ink"}>{changed ? "changed" : "unchanged"}</strong></div>; }