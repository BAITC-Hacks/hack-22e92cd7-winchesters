"use client";

import Link from "next/link";
import { useEffect, useState, useSyncExternalStore } from "react";
import { LevelChip } from "@/components/ledger/LevelChip";
import { ApiError, api } from "@/lib/api";
import type { CompetencyState } from "@/lib/ledger";
import type { CommitteeDecisionMemo } from "@/lib/types";
import { useAuth } from "@/lib/useAuth";
import { DemoChip, IllustrativeTag } from "@/components/ledger/Provenance";
import { Unavailable } from "@/components/ui/Unavailable";
import { SiteNav } from "@/components/site/SiteNav";

const noSubscription = () => () => {};
const DEFAULT_CANDIDATE = "c-001";

/** `?candidate=c-012` picks the memo; anything that is not a candidate ref falls back to the default. */
function candidateFromUrl(): string {
  const ref = new URLSearchParams(window.location.search).get("candidate") ?? "";
  return /^c-\d{3}$/.test(ref) ? ref : DEFAULT_CANDIDATE;
}

export default function DecisionMemoPage() {
  const { ready } = useAuth({ requireAuth: true, roles: ["committee", "admin"] });
  const [memo, setMemo] = useState<CommitteeDecisionMemo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [missing, setMissing] = useState<string | null>(null);
  const [locale, setLocale] = useState<"ru" | "kk">("ru");
  const candidateId = useSyncExternalStore(noSubscription, candidateFromUrl, () => null);

  useEffect(() => {
    if (!ready || !candidateId) return;
    api.committee.decisionMemo(candidateId, locale).then(setMemo).catch((cause) => {
      // 409: no stored ledger. A state, not a failure: nothing is built live.
      if (cause instanceof ApiError && cause.status === 409) setMissing(cause.message);
      else setError(cause instanceof ApiError && cause.status === 403 ? "This memo is for committee and admin only." : cause.message);
    });
  }, [ready, locale, candidateId]);

  const download = async () => {
    if (!candidateId) return;
    const url = URL.createObjectURL(await api.committee.decisionMemoPdf(candidateId, locale));
    const link = document.createElement("a");
    link.href = url;
    link.download = `decision-memo-${candidateId}.pdf`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const shell = (body: React.ReactNode) => (
    <div className="flex min-h-screen flex-col bg-canvas text-ink">
      <SiteNav />
      {body}
    </div>
  );
  if (!ready || !candidateId) return shell(<main className="p-8 text-sm text-ink-2">Checking access…</main>);
  if (error) return shell(<main className="p-8 text-sm text-danger">{error}</main>);
  if (missing) return shell(<Unavailable title="Committee decision memo" detail={`${missing}. The memo is a projection of a stored ledger; none is built live.`} />);
  if (!memo) return shell(<main className="p-8 text-sm text-ink-2">Loading decision memo…</main>);
  const signedRoles = new Set(memo.signatures.map((signature) => signature.role));
  const source = memo.ledger_provenance;
  const sign = async (role: "chair" | "member") => {
    await api.committee.signDecisionMemo(candidateId, role);
    setMemo(await api.committee.decisionMemo(candidateId, locale));
  };
  return shell(
    <main className="mx-auto w-full max-w-6xl px-4 py-8 md:px-10 md:py-10">
      <Link href="/dashboard" className="text-sm font-medium text-ink-2 hover:text-ink">
        ← Admissions Dashboard
      </Link>
      <header className="mt-4 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ink-2">Committee decision memo</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight md:text-4xl">{memo.title}</h1>
          <p className="mt-1.5 text-sm text-ink-2">
            {memo.candidate_label} {memo.candidate_id}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div role="radiogroup" aria-label="Memo language" className="flex gap-1 rounded-full border border-line bg-white p-1">
            {(
              [
                ["ru", "Русский"],
                ["kk", "Қазақша"],
              ] as const
            ).map(([key, label]) => (
              <button
                key={key}
                type="button"
                role="radio"
                aria-checked={locale === key}
                onClick={() => setLocale(key)}
                className={`rounded-full px-3.5 py-1.5 text-sm font-semibold transition-colors ${locale === key ? "bg-ink text-accent" : "text-ink-2 hover:text-ink"}`}
              >
                {label}
              </button>
            ))}
          </div>
          <button type="button" onClick={download} className="rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-ink transition-colors hover:bg-accent-strong">
            Download PDF
          </button>
        </div>
      </header>

      {source?.kind === "demo_mode" && <div className="mt-6"><DemoChip /></div>}
      {source && source.kind !== "demo_mode" && (
        <section data-slot="ledger-source" data-kind={source.kind} className={`mt-6 rounded-2xl bg-white px-5 py-4 text-sm ${source.illustrative ? "border-2 border-dashed border-ink-3" : "border border-line"}`}>
          <p className="font-semibold">{source.label}</p>
          <p className="mt-1 text-ink-2">{source.detail}</p>
        </section>
      )}

      <section className="mt-6 grid gap-3 sm:grid-cols-3">
        <Stat label={source?.illustrative ? "Example levels (not AI)" : source?.kind === "demo_mode" ? "Drafted (demo mode)" : "AI drafted"} value={`${memo.counts.ai_drafted} / ${memo.counts.items}`} />
        <Stat label="Committee changed" value={String(memo.counts.committee_changed)} />
        <Stat label="Bias probe" value={String(memo.probe_result.status).replace(/_/g, " ")} />
      </section>

      <section className="mt-6 grid gap-4 lg:grid-cols-2">
        {memo.competencies.map((item) => (
          <article key={item.competency} className="rounded-2xl border border-line bg-white p-5 md:p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-wider text-ink-3">{item.competency.replace(/_/g, " ")}</p>
                <h2 className="mt-1 text-lg font-semibold">{item.label}</h2>
              </div>
              <LevelChip small state={(item.effective_level ?? "reserved") as CompetencyState} />
            </div>
            <div className="mt-4 space-y-4">
              {item.indicators.flatMap((indicator) =>
                indicator.verified_quotes.map((quote) => (
                  <blockquote key={`${indicator.indicator_id}-${quote.quote}`} className="border-l-[3px] border-accent pl-3 text-sm leading-relaxed">
                    “{quote.quote}”
                    <footer className="mt-1 flex flex-wrap gap-2 text-xs text-ink-3">
                      <span>{indicator.indicator_id} · {quote.source}</span>
                      {source?.illustrative && <IllustrativeTag />}
                    </footer>
                  </blockquote>
                )),
              )}
            </div>
            <p className="mt-4 border-t border-line-soft pt-3 text-xs text-ink-2">
              <span className="font-semibold text-ink">Probe:</span> {item.probe_question}
            </p>
          </article>
        ))}
      </section>

      <section className="mt-6 grid gap-4 lg:grid-cols-2">
        <Panel title="Frozen provenance">
          <Hash label="Model" value={memo.provenance.model_hash} />
          <Hash label="Prompt" value={memo.provenance.prompt_hash} />
          <Hash label="Rubric" value={memo.provenance.rubric_hash} />
        </Panel>
        <Panel title="Committee signatures">
          <Signature role="chair" signed={signedRoles.has("chair")} onSign={sign} />
          <Signature role="member" signed={signedRoles.has("member")} onSign={sign} />
          {memo.signatures.map((signature) => (
            <p key={`${signature.role}-${signature.signed_at}`} className="text-xs text-ink-2">
              {signature.role}: {signature.name} · {new Date(signature.signed_at).toLocaleString()}
            </p>
          ))}
        </Panel>
      </section>
    </main>,
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-line bg-white p-5">
      <p className="text-xs uppercase tracking-wider text-ink-2">{label}</p>
      <p className="mt-2 text-3xl font-bold capitalize">{value}</p>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-line bg-white p-5 md:p-6">
      <h2 className="text-sm font-semibold uppercase tracking-wider">{title}</h2>
      <div className="mt-4 space-y-2 text-xs">{children}</div>
    </section>
  );
}

function Hash({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-ink-3">{label}</p>
      <p className="break-all font-mono">{value}</p>
    </div>
  );
}

function Signature({ role, signed, onSign }: { role: "chair" | "member"; signed: boolean; onSign: (role: "chair" | "member") => void }) {
  return (
    <div className="flex items-center justify-between border-b border-line-soft py-3 text-sm">
      <span>{role === "chair" ? "Председатель" : "Член комитета"}</span>
      {signed ? (
        <span className="rounded-full bg-accent-soft px-3 py-1 text-xs font-semibold text-accent-ink">✓ Signed</span>
      ) : (
        <button type="button" onClick={() => onSign(role)} className="rounded-full bg-ink px-4 py-1.5 text-xs font-semibold text-accent hover:opacity-90">
          Sign
        </button>
      )}
    </div>
  );
}
