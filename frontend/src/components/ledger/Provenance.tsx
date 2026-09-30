"use client";

import { createContext, useContext, type ReactNode } from "react";
import { CACHED_LEDGER_LABEL, DEMO_LEDGER_LABEL, ILLUSTRATIVE_LABEL, ILLUSTRATIVE_QUOTE_LABEL, isDemo, isIllustrative } from "@/lib/ledger";
import type { CandidateLedger } from "@/lib/types";

// LED-12: every stored ledger says where it came from, as plainly as the
// Scenario Lab says "cached demo transcript". Quotes inside an illustrative
// ledger read that context, so no view can show one as the applicant's own.
const IllustrativeContext = createContext(false);

export function LedgerProvenanceProvider({ ledger, children }: { ledger: CandidateLedger; children: ReactNode }) {
  return <IllustrativeContext.Provider value={isIllustrative(ledger)}>{children}</IllustrativeContext.Provider>;
}

export function useIllustrative(): boolean {
  return useContext(IllustrativeContext);
}

/** Banner above any ledger view: illustrative example, demo mode, or cached offline run. */
export function LedgerSourceBanner({ ledger }: { ledger: CandidateLedger }) {
  if (isIllustrative(ledger)) {
    return (
      <div data-slot="ledger-source" data-kind="illustrative_example" className="rounded-2xl border-2 border-dashed border-ink-3 bg-subtle px-4 py-3 text-sm">
        <p className="font-semibold text-ink">{ILLUSTRATIVE_LABEL}</p>
        <p className="mt-1 text-ink-2">
          Hand-authored for the LED-03 schema about a fictional applicant. The levels and every quote below, including
          the written-presentation quote, are not this applicant&apos;s; nothing here was scored.
        </p>
      </div>
    );
  }
  if (isDemo(ledger)) {
    return <DemoChip />;
  }
  return (
    <p data-slot="ledger-source" data-kind="cached_run" className="text-xs text-ink-2">
      <span className="font-medium text-ink">{CACHED_LEDGER_LABEL}.</span> Built once by {ledger.model_judge || "an unrecorded model"}{" "}
      and loaded from the LED-12 cache; no model was called for this view.
    </p>
  );
}

/** Small neutral chip for demo mode: the quotes are real, the model calls were stood in for. */
export function DemoChip() {
  return (
    <span
      data-slot="ledger-source"
      data-kind="demo_mode"
      title="Built without a model key: a stand-in replaced the two model calls. Quotes are the applicant's own words, checked against their documents."
      className="inline-block rounded-full border border-line px-2.5 py-0.5 text-[11px] text-ink-3"
    >
      {DEMO_LEDGER_LABEL}
    </span>
  );
}

/** Tag on a single quote that did not come from the applicant on screen. */
export function IllustrativeTag() {
  return (
    <span data-slot="illustrative-quote" className="rounded border border-dashed border-ink-3 px-1.5 text-ink-2 not-italic">
      {ILLUSTRATIVE_QUOTE_LABEL}
    </span>
  );
}
