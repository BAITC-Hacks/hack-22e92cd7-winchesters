"use client";

import { useEffect, useState } from "react";
import { LevelChip } from "@/components/ledger/LevelChip";
import { ApiError, api } from "@/lib/api";
import type { CompetencyState } from "@/lib/ledger";
import type { CommitteeDecisionMemo } from "@/lib/types";
import { useAuth } from "@/lib/useAuth";

export default function DecisionMemoPage() {
  const { ready } = useAuth({ requireAuth: true, roles: ["committee", "admin"] });
  const [memo, setMemo] = useState<CommitteeDecisionMemo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [locale, setLocale] = useState<"ru" | "kk">("ru");
  const candidateId = "c-001";

  useEffect(() => {
    if (!ready) return;
    api.committee.decisionMemo(candidateId, locale).then(setMemo).catch((cause) => setError(cause instanceof ApiError && cause.status === 403 ? "This memo is for committee and admin only." : cause.message));
  }, [ready, locale]);

  const download = async () => {
    const url = URL.createObjectURL(await api.committee.decisionMemoPdf(candidateId, locale));
    const link = document.createElement("a");
    link.href = url;
    link.download = `decision-memo-${candidateId}.pdf`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (!ready) return <main className="p-8 text-sm text-ink-2">Checking access...</main>;
  if (error) return <main className="p-8 text-sm text-danger">{error}</main>;
  if (!memo) return <main className="p-8 text-sm text-ink-2">Loading decision memo...</main>;
  const signedRoles = new Set(memo.signatures.map((signature) => signature.role));
  const sign = async (role: "chair" | "member") => { await api.committee.signDecisionMemo(candidateId, role); setMemo(await api.committee.decisionMemo(candidateId, locale)); };
  return <main className="min-h-screen bg-subtle px-5 py-8 text-ink sm:px-10"><div className="mx-auto max-w-6xl">
    <header className="flex flex-col gap-4 border-b-2 border-ink pb-5 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-ink-2">Committee decision memo</p><h1 className="mt-3 text-3xl font-semibold tracking-tight">{memo.title}</h1><p className="mt-2 text-sm text-ink-2">{memo.candidate_label} {memo.candidate_id}</p></div><div className="flex flex-wrap gap-2"><select aria-label="Memo language" value={locale} onChange={(event) => setLocale(event.target.value as "ru" | "kk")} className="border border-ink bg-white px-3 py-2 text-sm"><option value="ru">Русский</option><option value="kk">Қазақша</option></select><button onClick={download} className="border border-ink bg-accent-strong px-4 py-2 text-sm font-semibold">PDF</button></div></header>
    <section className="mt-6 grid gap-px bg-line sm:grid-cols-3"><Stat label="AI drafted" value={`${memo.counts.ai_drafted} / ${memo.counts.items}`} /><Stat label="Committee changed" value={String(memo.counts.committee_changed)} /><Stat label="Bias probe" value={String(memo.probe_result.status).replace(/_/g, " ")} /></section>
    <section className="mt-6 grid gap-6 lg:grid-cols-2">{memo.competencies.map((item) => <article key={item.competency} className="border border-line bg-white p-5"><div className="flex items-start justify-between gap-4"><div><p className="text-xs uppercase tracking-wider text-ink-3">{item.competency.replace(/_/g, " ")}</p><h2 className="mt-1 text-lg font-semibold">{item.label}</h2></div><LevelChip small state={(item.effective_level ?? "reserved") as CompetencyState} /></div><div className="mt-4 space-y-4">{item.indicators.flatMap((indicator) => indicator.verified_quotes.map((quote) => <blockquote key={`${indicator.indicator_id}-${quote.quote}`} className="border-l-2 border-accent-strong pl-3 text-sm leading-relaxed">“{quote.quote}”<footer className="mt-1 text-xs text-ink-3">{indicator.indicator_id} · {quote.source}</footer></blockquote>))}</div><p className="mt-4 border-t border-line-soft pt-3 text-xs text-ink-2">Probe: {item.probe_question}</p></article>)}</section>
    <section className="mt-6 grid gap-6 lg:grid-cols-2"><Panel title="Frozen provenance"><Hash label="Model" value={memo.provenance.model_hash} /><Hash label="Prompt" value={memo.provenance.prompt_hash} /><Hash label="Rubric" value={memo.provenance.rubric_hash} /></Panel><Panel title="Committee signatures"><Signature role="chair" signed={signedRoles.has("chair")} onSign={sign} /><Signature role="member" signed={signedRoles.has("member")} onSign={sign} />{memo.signatures.map((signature) => <p key={`${signature.role}-${signature.signed_at}`} className="text-xs text-ink-2">{signature.role}: {signature.name} · {new Date(signature.signed_at).toLocaleString()}</p>)}</Panel></section>
  </div></main>;
}

function Stat({ label, value }: { label: string; value: string }) { return <div className="bg-white p-5"><p className="text-xs uppercase tracking-wider text-ink-2">{label}</p><p className="mt-2 font-mono text-3xl">{value}</p></div>; }
function Panel({ title, children }: { title: string; children: React.ReactNode }) { return <section className="border border-line bg-white p-5"><h2 className="text-sm font-semibold uppercase tracking-wider">{title}</h2><div className="mt-4 space-y-2 text-xs">{children}</div></section>; }
function Hash({ label, value }: { label: string; value: string }) { return <div><p className="text-ink-3">{label}</p><p className="break-all font-mono">{value}</p></div>; }
function Signature({ role, signed, onSign }: { role: "chair" | "member"; signed: boolean; onSign: (role: "chair" | "member") => void }) { return <div className="flex items-center justify-between border-b border-[#eee] py-3 text-sm"><span>{role === "chair" ? "Председатель" : "Член комитета"}</span>{signed ? <strong className="text-[#527000]">Signed</strong> : <button onClick={() => onSign(role)} className="border border-ink px-3 py-1 text-xs font-semibold">Sign</button>}</div>; }