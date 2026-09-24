import type { EvidenceItem } from "@/lib/types";
import { ATOLA_LABELS, EVIDENCE_STATUS_LABELS, SOURCE_LABELS } from "./labels";

/** Slot for the indicator id (LED-06 decides how it is shown; never hidden). */
export function IndicatorId({ id }: { id: string }) {
  return (
    <code data-slot="indicator-id" className="text-xs font-mono text-[#5d5d5d] bg-[#f5f5f5] rounded px-1.5 py-0.5">
      {id}
    </code>
  );
}

/**
 * Slot for one verbatim quote with its provenance. The quote is printed exactly
 * as stored, in the applicant's language. An unverified quote should never reach
 * a card (the pipeline drops it), so if one does it is marked, not hidden.
 */
export function EvidenceQuote({ item, showAtola = true }: { item: EvidenceItem; showAtola?: boolean }) {
  const span = item.char_start >= 0 ? ` · ${item.char_start}–${item.char_end}` : "";
  return (
    <figure data-slot="quote" className="mb-2 last:mb-0">
      <blockquote
        className={`border-l-2 pl-3 italic ${item.verified ? "border-[#c1f11d] text-gray-700" : "border-red-300 text-gray-400 line-through"}`}
      >
        &ldquo;{item.quote}&rdquo;
      </blockquote>
      <figcaption className="pl-3 mt-0.5 text-xs text-[#969696] flex flex-wrap gap-x-2">
        <span>
          {SOURCE_LABELS[item.source]}
          {item.source_ref && ` · ${item.source_ref}`}
          {span}
        </span>
        {showAtola && item.atola !== "none" && <span>ATOLA: {ATOLA_LABELS[item.atola]}</span>}
        {item.status !== "present" && <span className="text-[#141414] font-medium">{EVIDENCE_STATUS_LABELS[item.status]}</span>}
        {!item.verified && <span className="text-red-600 font-medium">Not found in source</span>}
      </figcaption>
    </figure>
  );
}
