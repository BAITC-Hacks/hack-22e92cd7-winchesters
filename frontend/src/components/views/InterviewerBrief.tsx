import { atolaGaps, demonstratedEvidence, evidenceState, nineRows } from "@/lib/ledger";
import type { CandidateLedger, Competency, CompetencyRating, InterviewerPreBrief } from "@/lib/types";
import { EvidenceQuote } from "../ledger/EvidenceQuote";
import { IllustrativeTag } from "../ledger/Provenance";
import { ATOLA_LABELS, COMPETENCY_LABELS, EVIDENCE_STATE_LABELS } from "../ledger/labels";

export interface InterviewerBriefProps {
  ledger: CandidateLedger;
  preBrief?: InterviewerPreBrief;
}

/**
 * What the interviewer takes into the room. Deliberately without levels or
 * scores, so the interview is not anchored on the AI's reading: only what was
 * found, what is missing from each account, and what to ask. COM-03 turns this
 * into the phone and print one-pager (COM-02 layout).
 */
export function InterviewerBrief({ ledger, preBrief }: InterviewerBriefProps) {
  const rows = nineRows(ledger);
  const strengths = ledger.competencies
    .filter((r) => !r.reserved_for_humans)
    .flatMap((r) => demonstratedEvidence(r).map((e) => ({ ...e, competency: r.competency })))
    .slice(0, 2);

  return (
    <div className="space-y-6 print:space-y-3">
      <div className="rounded-xl bg-ink px-4 py-3 text-sm text-white">
        Do not name the competency aloud. Ask for a real situation, then ask about the parts of the story that are missing.
      </div>

      <section data-slot="strengths">
        <h4 className="text-sm font-semibold text-ink uppercase tracking-wider mb-2">Two strengths in their words</h4>
        {preBrief?.strengths.length ? (
          preBrief.strengths.map(({ competency, quote }, i) => (
            <div key={i} className="mb-2">
              <p className="text-xs text-ink-3">{COMPETENCY_LABELS[competency]}</p>
              <p className="border-l-4 border-accent pl-3 text-sm italic">&ldquo;{quote}&rdquo;</p>
              {preBrief.ledger_provenance?.illustrative && (
                <p className="pl-3 mt-0.5 text-xs">
                  <IllustrativeTag />
                </p>
              )}
            </div>
          ))
        ) : strengths.length > 0 ? (
          strengths.map(({ competency, item }, i) => (
            <div key={i} className="mb-2">
              <p className="text-xs text-ink-3">{COMPETENCY_LABELS[competency]}</p>
              <EvidenceQuote item={item} showAtola={false} />
            </div>
          ))
        ) : (
          <p className="text-sm text-ink-3 italic">No demonstrated behaviour in the written material yet.</p>
        )}
      </section>

      <section>
        <h4 className="text-sm font-semibold text-ink uppercase tracking-wider mb-2">What to ask</h4>
        <div className="divide-y divide-line-soft rounded-2xl border border-line bg-white">
          {rows.map(({ competency, rating }) => (
            <BriefRow key={competency} competency={competency} rating={rating} preBrief={preBrief?.rows.find((row) => row.competency === competency)} />
          ))}
        </div>
      </section>
    </div>
  );
}

function BriefRow({ competency, rating, preBrief }: { competency: Competency; rating?: CompetencyRating; preBrief?: InterviewerPreBrief["rows"][number] }) {
  const state = evidenceState(rating);
  const gaps = rating && !rating.reserved_for_humans ? atolaGaps(rating) : [];
  const flags = preBrief?.discrepancy_alerts ?? rating?.flags ?? [];
  const ask = preBrief?.probe?.paraphrase ?? rating?.probe_question ?? "";
  const hasMore = Boolean(preBrief?.probe) || flags.length > 0;

  return (
    <div className="break-inside-avoid px-4 py-4 text-sm">
      <div className="flex items-center justify-between gap-3">
        <span className={`font-semibold ${rating ? "text-ink" : "text-ink-3"}`}>{COMPETENCY_LABELS[competency]}</span>
        <span data-slot="evidence-state" data-state={state} className="whitespace-nowrap rounded-full bg-subtle px-2.5 py-0.5 text-xs text-ink-2">
          {EVIDENCE_STATE_LABELS[state]}
        </span>
      </div>

      {/* All five missing says nothing the state does not; only a partial story has gaps worth naming. */}
      {gaps.length > 0 && gaps.length < 5 && (
        <p data-slot="atola" className="mt-1.5 text-xs text-ink-3">
          Missing from their story: {gaps.map((c) => ATOLA_LABELS[c]).join(" · ")}
        </p>
      )}

      {ask && (
        <p data-slot="probe" className="mt-2 rounded-xl bg-accent-soft px-3 py-2 text-ink">
          <span className="font-semibold">Ask: </span>
          {ask}
        </p>
      )}

      {hasMore && (
        <details className="mt-2 text-xs text-ink-2">
          <summary className="cursor-pointer select-none hover:text-ink">More for the interviewer</summary>
          <div className="mt-2 space-y-2">
            {preBrief?.probe && (
              <>
                <p><span className="font-medium">Canonical probe: </span>{preBrief.probe.canonical}</p>
                <p data-slot="allowed-paraphrases"><span className="font-medium">Allowed wording: </span>{preBrief.probe.allowed_paraphrases.join(" / ")}</p>
              </>
            )}
            {flags.length > 0 && (
              <ul data-slot="flags" className="space-y-1">
                {flags.map((f, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="mt-0.5 size-3.5 shrink-0 rounded-sm border border-ink-3" aria-hidden />
                    <span>{f.quote && <q className="italic">{f.quote}</q>} {f.explanation}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </details>
      )}
    </div>
  );
}
