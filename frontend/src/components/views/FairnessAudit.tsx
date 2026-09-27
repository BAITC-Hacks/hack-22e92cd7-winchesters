"use client";

import { useMemo, useState } from "react";
import { ledgerStats, type CompetencyState } from "@/lib/ledger";
import type { CandidateLedger } from "@/lib/types";
import { CollapsiblePanel } from "../ui/CollapsiblePanel";
import { AttributeAudit } from "../fairness/AttributeAudit";
import { LevelChip } from "../ledger/LevelChip";

export interface FairnessAuditProps {
  ledgers: CandidateLedger[];
}

type AuditViewMode = "blind" | "informed";

const INFORMED_ATTRIBUTES = [
  "School type",
  "Region and settlement",
  "Application language",
  "Foundation eligibility",
  "Gender",
];

/**
 * Cohort-level checks. Two parts with very different standing:
 *
 * - Ledger health: how often the pipeline abstained, capped or found nothing.
 *   Counts only; a level is never averaged.
 * - The attribute-grouped audit (FAIR-07): impact ratios by declared background.
 */
export function FairnessAudit({ ledgers }: FairnessAuditProps) {
  const [mode, setMode] = useState<AuditViewMode>("blind");

  return (
    <CollapsiblePanel icon="/assets/Scales.svg" title="Fairness Audit">
      <div className="space-y-6">
        <div className="flex flex-col gap-3 border-b border-[#eee] pb-4 sm:flex-row sm:items-start sm:justify-between" data-mode={mode}>
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-wider text-ink">Committee view</p>
            <p className="mt-1 text-xs leading-relaxed text-ink-2">
              {mode === "blind"
                ? "Candidate context is hidden while reviewing evidence."
                : "Context is visible for fairness review only; it is excluded from scoring."}
            </p>
          </div>
          <div className="flex shrink-0 self-start rounded-[10px] bg-muted p-1 gap-1" role="radiogroup" aria-label="Fairness audit view">
            {(["blind", "informed"] as const).map((viewMode) => (
              <button
                key={viewMode}
                type="button"
                role="radio"
                aria-checked={mode === viewMode}
                onClick={() => setMode(viewMode)}
                className={`px-3 py-1.5 rounded-[8px] text-[13px] font-semibold capitalize ${mode === viewMode ? "bg-ink text-accent" : "text-ink"}`}
              >
                {viewMode}
              </button>
            ))}
          </div>
        </div>

        <div
          className={`border px-3 py-2.5 text-xs leading-relaxed ${mode === "blind" ? "border-line bg-subtle text-ink-2" : "border-accent bg-[#f7fbdc] text-accent-ink"}`}
          data-slot="context-strip"
          role="status"
        >
          {mode === "blind" ? (
            <span>Blind: candidate context is withheld from this committee-facing view.</span>
          ) : (
            <span>
              Informed: fairness-only context available: {INFORMED_ATTRIBUTES.join(", ")}. These attributes do not enter
              scoring or recommendation; changing this view cannot prove fairness.
            </span>
          )}
        </div>

        <div data-slot="attribute-audit">
          <AttributeAudit />
        </div>
        <LedgerHealth ledgers={ledgers} />
      </div>
    </CollapsiblePanel>
  );
}
const STATE_ORDER: CompetencyState[] = [
  "high",
  "normal",
  "weak",
  "no_evidence",
  "reserved",
  "not_in_ledger",
];

function LedgerHealth({ ledgers }: { ledgers: CandidateLedger[] }) {
  const s = useMemo(() => ledgerStats(ledgers), [ledgers]);
  const facts: [string, number, string][] = [
    [
      "Indicators without verified evidence",
      s.indicatorsWithoutEvidence,
      `of ${s.indicators}`,
    ],
    [
      "Indicators capped (claimed, not shown)",
      s.cappedIndicators,
      `of ${s.indicators}`,
    ],
    [
      "Quotes that failed verification",
      s.unverifiedItems,
      `of ${s.evidenceItems}`,
    ],
    ["Attention flags for interviewers", s.flags, ""],
  ];
  return (
    <section>
      <h4 className="text-sm font-semibold text-ink uppercase tracking-wider mb-1">
        Ledger health
      </h4>
      <p className="text-xs text-ink-3 mb-3">
        {s.ledgers} ledger{s.ledgers === 1 ? "" : "s"} × 9 competencies. Until
        LED-11 this is the LED-03 fixture.
      </p>
      <div className="flex flex-wrap gap-3 mb-4">
        {STATE_ORDER.map((state) => (
          <div key={state} className="flex items-center gap-2">
            <LevelChip state={state} small />
            <span className="font-mono text-sm text-ink">
              {s.competencyStates[state]}
            </span>
          </div>
        ))}
      </div>
      <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-1 text-sm">
        {facts.map(([label, value, of]) => (
          <div
            key={label}
            className="flex justify-between border-b border-[#eee] py-1"
          >
            <dt className="text-ink-2">{label}</dt>
            <dd className="font-mono text-ink">
              {value} <span className="text-ink-3">{of}</span>
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
