import { competencyState, demonstratedEvidence } from "@/lib/ledger";
import type { CandidateLedger, Competency } from "@/lib/types";
import { EvidenceQuote } from "../ledger/EvidenceQuote";
import { COMPETENCY_LABELS } from "../ledger/labels";

export interface GrowthMapProps {
  ledger: CandidateLedger;
}

// Suppressed by default in anything the applicant sees (CAND-02).
const SUPPRESSED: Competency[] = ["wounded_leadership"];

/**
 * A draft of the applicant-facing Growth Map, derived from the ledger so the
 * committee can see what it would say. No level names, no comparisons, no
 * anchor wording: those are committee vocabulary (CAND-05). The real map is
 * generated per language behind a release gate by CAND-02 and rendered by
 * CAND-03; the slots here are where that text goes.
 */
export function GrowthMap({ ledger }: GrowthMapProps) {
  const visible = ledger.competencies.filter((r) => !r.reserved_for_humans && !SUPPRESSED.includes(r.competency));

  const strengths = visible
    .filter((r) => {
      const s = competencyState(r);
      return s === "high" || s === "normal";
    })
    // One quote per competency, the first behaviour found: a preview, not the full ledger.
    .flatMap((r) => demonstratedEvidence(r).slice(0, 1).map((e) => ({ ...e, competency: r.competency })));
  const growing = visible.filter((r) => competencyState(r) === "weak").map((r) => r.competency);
  const notYetSeen = visible.filter((r) => competencyState(r) === "no_evidence").map((r) => r.competency);

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-dashed border-ink-3 px-4 py-3 text-sm text-ink-2">
        <span className="font-semibold text-ink">Preview of the applicant&apos;s feedback.</span> They see nothing until a
        committee member approves it. It never shows levels, and wounded leadership is never shown.
      </div>

      <section data-slot="growth-strengths">
        <h4 className="text-sm font-semibold text-ink uppercase tracking-wider mb-2">What we saw you do</h4>
        {strengths.length > 0 ? (
          strengths.map(({ competency, item }, i) => (
            <div key={i} className="mb-3">
              <p className="text-xs text-ink-3">{COMPETENCY_LABELS[competency]}</p>
              <EvidenceQuote item={item} showAtola={false} />
            </div>
          ))
        ) : (
          <p className="text-sm text-ink-3 italic">Nothing to quote yet.</p>
        )}
      </section>

      <GrowthList
        slot="growth-next"
        title="Where to grow next"
        competencies={growing}
        placeholder="A concrete next step they can take, with no cost."
      />
      <GrowthList
        slot="growth-not-yet-seen"
        title="Not yet seen"
        competencies={notYetSeen}
        placeholder="Your application did not show this yet. That is an opportunity, not a mark against you."
      />
    </div>
  );
}

function GrowthList({
  slot,
  title,
  competencies,
  placeholder,
}: {
  slot: string;
  title: string;
  competencies: Competency[];
  placeholder: string;
}) {
  if (competencies.length === 0) return null;
  return (
    <section data-slot={slot}>
      <h4 className="text-sm font-semibold text-ink uppercase tracking-wider mb-2">{title}</h4>
      <ul className="space-y-2">
        {competencies.map((c) => (
          <li key={c} className="rounded-xl bg-subtle px-4 py-3 text-sm">
            <p className="font-medium text-ink">{COMPETENCY_LABELS[c]}</p>
            <p className="text-ink-3 italic">{placeholder}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
