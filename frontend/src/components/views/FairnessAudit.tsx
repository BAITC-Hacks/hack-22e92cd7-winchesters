"use client";

import { useMemo } from "react";
import { ledgerStats, type CompetencyState } from "@/lib/ledger";
import type { CandidateLedger } from "@/lib/types";
import { CollapsiblePanel } from "../ui/CollapsiblePanel";
import { AttributeAudit } from "../fairness/AttributeAudit";
import { LevelChip } from "../ledger/LevelChip";

export interface FairnessAuditProps {
  ledgers: CandidateLedger[];
}

/**
 * Cohort-level checks. Two parts with very different standing:
 *
 * - Ledger health: how often the pipeline abstained, capped or found nothing.
 *   Counts only; a level is never averaged.
 * - The attribute-grouped audit (FAIR-07): impact ratios by declared background.
 */
export function FairnessAudit({ ledgers }: FairnessAuditProps) {
  return (
    <CollapsiblePanel icon="/assets/Scales.svg" title="Fairness Audit">
      <div className="space-y-6">
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
      <h4 className="text-sm font-semibold text-[#141414] uppercase tracking-wider mb-1">
        Ledger health
      </h4>
      <p className="text-xs text-[#969696] mb-3">
        {s.ledgers} ledger{s.ledgers === 1 ? "" : "s"} × 9 competencies. Until
        LED-11 this is the LED-03 fixture.
      </p>
      <div className="flex flex-wrap gap-3 mb-4">
        {STATE_ORDER.map((state) => (
          <div key={state} className="flex items-center gap-2">
            <LevelChip state={state} small />
            <span className="font-mono text-sm text-[#141414]">
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
            <dt className="text-[#5d5d5d]">{label}</dt>
            <dd className="font-mono text-[#141414]">
              {value} <span className="text-[#969696]">{of}</span>
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
