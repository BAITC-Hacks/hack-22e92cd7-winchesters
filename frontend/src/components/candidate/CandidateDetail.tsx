"use client";

import { useState, type ReactNode } from "react";
import type { Scorer } from "@/lib/dashboard";
import { useOverrides } from "@/lib/useOverrides";
import type {
  AIDetectionResult,
  Candidate,
  CandidateLedger,
  InterviewerPreBrief,
  CandidateScore,
  CounterfactualProbeResult,
  FeynmanScore,
  VideoAnalysis,
} from "@/lib/types";
import { CommitteeCard } from "../views/CommitteeCard";
import { CounterfactualProbe } from "./CounterfactualProbe";
import { GrowthMap } from "../views/GrowthMap";
import { InterviewerBrief } from "../views/InterviewerBrief";
import { ApplicationProfile } from "./ApplicationProfile";
import { FeynmanPanel } from "./FeynmanPanel";
import { ScoreBreakdown } from "./ScoreBreakdown";
import { SourceConsistencyPanel } from "./SourceConsistencyPanel";
import { VideoPanel } from "./VideoPanel";
import { WrittenPresentationMissing } from "./WrittenPresentation";

type Tab = "application" | "committee" | "interviewer" | "growth";

const TABS: { key: Tab; label: string }[] = [
  { key: "application", label: "Application" },
  { key: "committee", label: "Committee Card" },
  { key: "interviewer", label: "Interviewer Brief" },
  { key: "growth", label: "Growth Map" },
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
  feynmanScore: FeynmanScore | null;
  videoAnalysis: VideoAnalysis | null;
  counterfactualProbe: CounterfactualProbeResult | null;
  probeLoading: boolean;
  probeError: string | null;
  detectLoading: boolean;
  onClose: () => void;
  onDetectAI: () => void;
  onAnalyzeVideo: () => void;
  onRunProbe: () => void;
}

export function CandidateDetail(props: CandidateDetailProps) {
  const { candidate: c, onClose } = props;
  const [tab, setTab] = useState<Tab>("application");
  const overrides = useOverrides(c.id);

  return (
    <div className="fixed inset-0 flex items-center justify-center p-6" style={{ zIndex: 200 }}>
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div
        className="relative w-full max-w-4xl max-h-[90vh] bg-white shadow-2xl overflow-y-auto"
        style={{ borderRadius: "20px", border: "2.7px solid #d7d7d7" }}
      >
        <div className="sticky top-0 bg-white z-10 px-8 pt-5 border-b border-line">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-ink">{c.name}</h2>
              <p className="text-base text-ink-2">
                {c.id} &middot; Age {c.age}
              </p>
            </div>
            <button
              className="w-10 h-10 rounded-full bg-muted hover:bg-ink hover:text-white text-ink flex items-center justify-center text-xl transition-colors"
              onClick={onClose}
            >
              &times;
            </button>
          </div>
          <div role="tablist" className="flex gap-1 mt-4 -mb-px overflow-x-auto">
            {TABS.map((t) => (
              <button
                key={t.key}
                role="tab"
                aria-selected={tab === t.key}
                onClick={() => setTab(t.key)}
                className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-[3px] transition-colors ${
                  tab === t.key ? "border-accent text-ink" : "border-transparent text-ink-3 hover:text-ink"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        <div className="p-8 space-y-8">
          {tab === "application" && <ApplicationTab {...props} />}
          {tab === "committee" && (
            <LedgerGate
              {...props}
              render={(l) => (
                <>
                  {!c.written_presentation && <WrittenPresentationMissing />}
                  <CommitteeCard ledger={l} overrides={overrides} />
                </>
              )}
            />
          )}
          {tab === "interviewer" && <LedgerGate {...props} render={(l) => <InterviewerBrief ledger={l} preBrief={props.preBrief} />} />}
          {tab === "growth" && <LedgerGate {...props} render={(l) => <GrowthMap ledger={l} />} />}
        </div>
      </div>
    </div>
  );
}

function ApplicationTab(props: CandidateDetailProps) {
  const { candidate, scorer, score } = props;
  return (
    <>
      <ApplicationProfile candidate={candidate} />
      {score && <ScoreBreakdown score={score} scorer={scorer} />}
      <CounterfactualProbe
        result={props.counterfactualProbe}
        loading={props.probeLoading}
        error={props.probeError}
        onRun={props.onRunProbe}
      />
      <SourceConsistencyPanel result={props.aiDetection} loading={props.detectLoading} onRun={props.onDetectAI} />
      <VideoPanel analysis={props.videoAnalysis} onRun={props.onAnalyzeVideo} />
      <FeynmanPanel key={candidate.id} score={props.feynmanScore} />
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
      <p className="p-4 bg-gray-500/5 text-ink-2 rounded-2xl text-sm border border-gray-500/20">
        No evidence ledger has been built for this candidate yet. Nothing is scored live; the committee card appears
        once a cached run is loaded.
      </p>
    );
  }
  if (ledgerError) {
    return <p className="p-4 bg-red-500/10 text-red-600 rounded-2xl text-sm border border-red-500/20">{ledgerError}</p>;
  }
  if (!ledger) return <p className="text-center py-10 text-ink-3">Loading ledger...</p>;
  return <div className="space-y-4">{render(ledger)}</div>;
}
