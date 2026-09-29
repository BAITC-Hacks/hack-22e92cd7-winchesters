"use client";

import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";
import type { Scorer } from "@/lib/dashboard";
import { useOverrides } from "@/lib/useOverrides";
import type {
  AIDetectionResult,
  Candidate,
  CandidateLedger,
  InterviewerPreBrief,
  CandidateScore,
  CounterfactualProbeResult,
  ScenarioResult,
} from "@/lib/types";
import { CommitteeCard } from "../views/CommitteeCard";
import { CounterfactualProbe } from "./CounterfactualProbe";
import { GrowthMap } from "../views/GrowthMap";
import { LedgerProvenanceProvider, LedgerSourceBanner } from "../ledger/Provenance";
import { InterviewerBrief } from "../views/InterviewerBrief";
import { ApplicationProfile } from "./ApplicationProfile";
import { ScenarioPanel } from "./ScenarioPanel";
import { ScoreBreakdown } from "./ScoreBreakdown";
import { SourceConsistencyPanel } from "./SourceConsistencyPanel";

type Tab = "application" | "committee" | "interviewer" | "growth";

// The evidence first: the drawer opens on the committee card.
const TABS: { key: Tab; label: string }[] = [
  { key: "committee", label: "Committee Card" },
  { key: "interviewer", label: "Interviewer Brief" },
  { key: "growth", label: "Growth Map" },
  { key: "application", label: "Application" },
];

export interface CandidateDetailProps {
  candidate: Candidate;
  scorer: Scorer;
  score: CandidateScore | null;
  /** undefined while loading. */
  ledger: CandidateLedger | undefined;
  preBrief: InterviewerPreBrief | undefined;
  ledgerError: string | null;
  /** No stored snapshot for this candidate (404); the API never builds one live. */
  ledgerMissing: boolean;
  aiDetection: AIDetectionResult | null;
  scenarioResult: ScenarioResult | null;
  counterfactualProbe: CounterfactualProbeResult | null;
  probeLoading: boolean;
  probeError: string | null;
  detectLoading: boolean;
  onClose: () => void;
  onDetectAI: () => void;
  onRunProbe: () => void;
}

export function CandidateDetail(props: CandidateDetailProps) {
  const { candidate: c, onClose } = props;
  const [tab, setTab] = useState<Tab>("committee");
  const overrides = useOverrides(c.id);

  useEffect(() => {
    const closeOnEscape = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-[200] flex justify-end" role="dialog" aria-modal="true" aria-label={c.name}>
      <div className="absolute inset-0 bg-ink/40 backdrop-blur-[2px]" onClick={onClose} />
      <aside className="drawer-in relative flex h-full w-full max-w-[920px] flex-col bg-white shadow-2xl">
        <div className="shrink-0 border-b border-line bg-white px-5 pt-5 md:px-8">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <h2 className="truncate text-2xl font-bold text-ink">{c.name}</h2>
              <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-sm text-ink-2">
                <span>
                  {c.id} &middot; Age {c.age}
                </span>
                {c.application.languages.map((lang) => (
                  <span key={lang} className="rounded border border-line px-1.5 py-px text-xs text-ink-2">
                    {lang}
                  </span>
                ))}
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              {props.ledger && (
                <Link
                  href={`/decision-memo?candidate=${c.id}`}
                  className="hidden rounded-full bg-ink px-4 py-2 text-sm font-semibold text-accent transition-opacity hover:opacity-90 sm:inline-block"
                >
                  Decision memo →
                </Link>
              )}
            <button
              type="button"
              aria-label="Close"
              className="flex size-10 shrink-0 items-center justify-center rounded-full border border-line text-xl text-ink transition-colors hover:border-ink"
              onClick={onClose}
            >
              &times;
            </button>
            </div>
          </div>
          <div role="tablist" className="-mb-px mt-4 flex gap-1 overflow-x-auto">
            {TABS.map((t) => (
              <button
                key={t.key}
                role="tab"
                aria-selected={tab === t.key}
                onClick={() => setTab(t.key)}
                className={`whitespace-nowrap border-b-[3px] px-4 py-2.5 text-sm font-semibold transition-colors ${
                  tab === t.key ? "border-ink text-ink" : "border-transparent text-ink-3 hover:text-ink"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 space-y-8 overflow-y-auto p-5 md:p-8">
          {tab === "application" && <ApplicationTab {...props} />}
          {tab === "committee" && (
            <LedgerGate
              {...props}
              render={(l) => (
                <CommitteeCard ledger={l} overrides={overrides} scenario={props.scenarioResult} />
              )}
            />
          )}
          {tab === "interviewer" && <LedgerGate {...props} render={(l) => <InterviewerBrief ledger={l} preBrief={props.preBrief} />} />}
          {tab === "growth" && <LedgerGate {...props} render={(l) => <GrowthMap ledger={l} />} />}
        </div>
      </aside>
    </div>
  );
}

function ApplicationTab(props: CandidateDetailProps) {
  const { candidate, scorer, score } = props;
  return (
    <>
      <ApplicationProfile candidate={candidate} />
      {/* The completeness figures are on the dashboard card; only an AI score adds something here. */}
      {score && scorer === "ai" && <ScoreBreakdown score={score} scorer={scorer} />}
      <h3 className="border-t border-line pt-6 text-xs font-semibold uppercase tracking-wider text-ink-2">Checks</h3>
      <CounterfactualProbe
        result={props.counterfactualProbe}
        loading={props.probeLoading}
        error={props.probeError}
        onRun={props.onRunProbe}
      />
      <SourceConsistencyPanel result={props.aiDetection} loading={props.detectLoading} onRun={props.onDetectAI} />
      <ScenarioPanel result={props.scenarioResult} />
    </>
  );
}

function LedgerGate({
  ledger,
  ledgerError,
  ledgerMissing,
  render,
}: CandidateDetailProps & { render: (ledger: CandidateLedger) => ReactNode }) {
  if (ledgerMissing) {
    return (
      <p data-slot="ledger-unavailable" className="p-4 bg-subtle text-ink-2 rounded-2xl text-sm border border-line">
        Unavailable — nothing was scored. No evidence ledger has been built for this candidate yet, and none is built
        live; this view appears once a cached run is loaded.
      </p>
    );
  }
  if (ledgerError) {
    return <p className="p-4 bg-red-500/10 text-red-600 rounded-2xl text-sm border border-red-500/20">{ledgerError}</p>;
  }
  if (!ledger) return <p className="text-center py-10 text-ink-3">Loading ledger...</p>;
  return (
    <LedgerProvenanceProvider ledger={ledger}>
      <div className="space-y-4">
        <LedgerSourceBanner ledger={ledger} />
        {render(ledger)}
      </div>
    </LedgerProvenanceProvider>
  );
}
