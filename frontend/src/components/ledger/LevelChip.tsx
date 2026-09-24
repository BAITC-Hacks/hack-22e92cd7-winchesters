import type { CompetencyState } from "@/lib/ledger";
import { STATE_LABELS } from "./labels";

// Placeholder styling until LED-07 delivers the BARS visual system. The one
// rule that must survive the redesign: "no evidence" never looks like "weak"
// (dashed outline, not a fill), and nothing here is a number.
const STYLES: Record<CompetencyState, string> = {
  high: "bg-[#c1f11d] text-[#141414] border-[#c1f11d]",
  normal: "bg-[#eae9e9] text-[#141414] border-[#eae9e9]",
  weak: "bg-[#5d5d5d] text-white border-[#5d5d5d]",
  no_evidence: "bg-white text-[#5d5d5d] border-dashed border-[#969696]",
  reserved: "bg-[#141414] text-white border-[#141414]",
  not_in_ledger: "bg-white text-[#969696] border-dotted border-[#d7d7d7]",
};

/** Slot for the BARS level chip (LED-07). */
export function LevelChip({ state, small = false }: { state: CompetencyState; small?: boolean }) {
  return (
    <span
      data-slot="bars-chip"
      data-level={state}
      className={`inline-block border-2 rounded-full font-medium whitespace-nowrap ${small ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-sm"} ${STYLES[state]}`}
    >
      {STATE_LABELS[state]}
    </span>
  );
}
