"use client";

import type { EvidenceItem } from "@/lib/types";
import { ATOLA_LABELS, EVIDENCE_STATUS_LABELS, SOURCE_LABELS } from "./labels";
import { IllustrativeTag, useIllustrative } from "./Provenance";

/** Slot for the indicator id (LED-06 decides how it is shown; never hidden). */
export function IndicatorId({ id }: { id: string }) {
  return (
    <code data-slot="indicator-id" className="text-xs font-mono text-ink-2 bg-subtle rounded px-1.5 py-0.5">
      {id}
    </code>
  );
}

/**
 * One verbatim quote, printed exactly as stored in the applicant's language,
 * with where it came from. An unverified quote should never reach a card (the
 * pipeline drops it), so if one does it is marked, not hidden.
 */
export function EvidenceQuote({
  item,
  indicator,
  showAtola = false,
}: {
  item: EvidenceItem;
  /** Readable name of the behaviour this quote speaks to. */
  indicator?: string;
  showAtola?: boolean;
}) {
  const illustrative = useIllustrative();
  return (
    <figure data-slot="quote" className="mb-3 last:mb-0">
      <blockquote
        className={`border-l-[3px] pl-3 leading-relaxed ${item.verified ? "border-accent text-ink" : "border-danger/40 text-ink-3 line-through"}`}
      >
        &ldquo;{item.quote}&rdquo;
      </blockquote>
      <figcaption className="mt-1 flex flex-wrap gap-x-2 gap-y-1 pl-3 text-xs text-ink-3">
        <span>{SOURCE_LABELS[item.source]}</span>
        {indicator && <span>· {indicator}</span>}
        {showAtola && item.atola !== "none" && <span>· {ATOLA_LABELS[item.atola]}</span>}
        {item.status !== "present" && (
          <span className="rounded bg-muted px-1.5 font-medium text-ink-2">{EVIDENCE_STATUS_LABELS[item.status]}</span>
        )}
        {!item.verified && <span className="font-medium text-danger">Not found in source</span>}
        {illustrative && <IllustrativeTag />}
      </figcaption>
    </figure>
  );
}
