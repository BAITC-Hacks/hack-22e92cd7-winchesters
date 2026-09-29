"use client";

import { useMemo } from "react";
import { isDemo, isIllustrative, ledgerStats } from "@/lib/ledger";
import type { CandidateLedger } from "@/lib/types";
import { CollapsiblePanel } from "../ui/CollapsiblePanel";
import { AttributeAudit } from "../fairness/AttributeAudit";

export interface FairnessAuditProps {
  ledgers: CandidateLedger[];
}

export function FairnessAudit({ ledgers }: FairnessAuditProps) {
  return (
    <CollapsiblePanel icon="/assets/icons/fairness.svg" title="Fairness Audit">
      <div className="space-y-8">
        <p className="max-w-2xl text-sm text-ink-2">
          Each applicant is rated on their own. This page checks the AI itself: whether whole groups of applicants, for
          example rural students writing in Kazakh, get lower levels than others. Background never enters scoring; this
          is how we would notice if it leaked in anyway.
        </p>
        <div data-slot="attribute-audit">
          <AttributeAudit />
        </div>
        <LedgerHealth ledgers={ledgers} />
      </div>
    </CollapsiblePanel>
  );
}

function LedgerHealth({ ledgers }: { ledgers: CandidateLedger[] }) {
  // The hand-authored example is about nobody in this cohort: counting it
  // would print cohort figures with no source (LED-12).
  const cached = useMemo(() => ledgers.filter((l) => !isIllustrative(l)), [ledgers]);
  const excluded = ledgers.length - cached.length;
  const s = useMemo(() => ledgerStats(cached), [cached]);
  const demoCount = cached.filter(isDemo).length;
  if (cached.length === 0) {
    return (
      <section data-slot="ledger-health" data-state="unavailable">
        <h4 className="mb-2 text-sm font-semibold text-ink">Evidence checks</h4>
        <p className="rounded-2xl border border-line bg-subtle px-4 py-3 text-sm text-ink-2">
          Unavailable — nothing was scored. No cached ledger run is loaded yet
          {excluded > 0 ? `; the ${excluded} illustrative worked example is not counted as cohort data` : ""}.
        </p>
      </section>
    );
  }
  const matched = s.evidenceItems - s.unverifiedItems;
  const facts: [string, string][] = [
    [`${matched} of ${s.evidenceItems}`, "quotes found word for word in the applicants' own texts"],
    [String(s.competencyStates.no_evidence), "competency ratings with no evidence yet, left for the interview"],
    [String(s.cappedIndicators), "claims kept at Normal because no real example was given"],
  ];
  return (
    <section data-slot="ledger-health">
      <h4 className="text-sm font-semibold text-ink">Evidence checks</h4>
      <p className="mb-3 mt-0.5 text-xs text-ink-3">
        Across {s.ledgers} applicant{s.ledgers === 1 ? "" : "s"}
        {demoCount === s.ledgers ? ", built in demo mode without a live model" : demoCount > 0 ? ` (${demoCount} in demo mode)` : ""}
        {excluded > 0 ? `; ${excluded} illustrative example not counted` : ""}.
      </p>
      <div className="grid gap-3 sm:grid-cols-3">
        {facts.map(([value, label]) => (
          <div key={label} className="rounded-2xl border border-line bg-white p-4">
            <p className="text-2xl font-bold text-ink">{value}</p>
            <p className="mt-1 text-xs text-ink-2">{label}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
