import type { CompetencyState } from "@/lib/ledger";
import { STATE_LABELS } from "./labels";

// BARS visual system (LED-07). Levels are ordinal, so they read as a
// three-step meter first and a colour second: weak ●○○, normal ●●○, high ●●●.
// Weak is deliberately quiet (it is a finding, not an alarm), only high uses the
// brand accent, and "no evidence" is an empty dashed meter so it can never be
// mistaken for weak. Reserved and not-assessed carry no meter at all: nothing
// here is a number.
const STEPS: Partial<Record<CompetencyState, number>> = { weak: 1, normal: 2, high: 3, no_evidence: 0 };

const CHIP: Record<CompetencyState, string> = {
  high: "bg-accent border-accent text-ink",
  normal: "bg-white border-ink text-ink",
  weak: "bg-white border-line text-ink-2",
  no_evidence: "bg-white border-dashed border-ink-3 text-ink-2",
  reserved: "bg-ink border-ink text-white",
  not_in_ledger: "bg-subtle border-dotted border-line text-ink-3",
};

const DOT_ON: Record<CompetencyState, string> = {
  high: "bg-ink",
  normal: "bg-ink",
  weak: "bg-ink-2",
  no_evidence: "",
  reserved: "",
  not_in_ledger: "",
};

export function LevelChip({ state, small = false }: { state: CompetencyState; small?: boolean }) {
  const steps = STEPS[state];
  return (
    <span
      data-slot="bars-chip"
      data-level={state}
      className={`inline-flex items-center gap-1.5 border-2 rounded-full font-medium whitespace-nowrap ${small ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-sm"} ${CHIP[state]}`}
    >
      {steps !== undefined && (
        <span className="inline-flex gap-0.5" aria-hidden>
          {[1, 2, 3].map((i) => (
            <span
              key={i}
              className={`rounded-full ${small ? "size-1.5" : "size-2"} ${
                i <= steps ? DOT_ON[state] : state === "no_evidence" ? "border border-dashed border-ink-3" : "bg-line"
              }`}
            />
          ))}
        </span>
      )}
      {STATE_LABELS[state]}
    </span>
  );
}
