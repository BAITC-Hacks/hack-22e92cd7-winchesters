import { ATOLA_SEQUENCE, atolaGaps, demonstratedEvidence, evidenceState, nineRows } from "@/lib/ledger";
import type { CandidateLedger, Competency, CompetencyRating, InterviewerPreBrief } from "@/lib/types";
import { EvidenceQuote } from "../ledger/EvidenceQuote";
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
      <div className="rounded-xl bg-[#141414] text-white px-4 py-3 text-sm">
        Do not name the competency aloud. Ask for a situation, then follow the missing parts of the story.
      </div>

      <section data-slot="strengths">
        <h4 className="text-sm font-semibold text-[#141414] uppercase tracking-wider mb-2">Two strengths in their words</h4>
        {preBrief?.strengths.length ? (
          preBrief.strengths.map(({ competency, quote }, i) => (
            <div key={i} className="mb-2">
              <p className="text-xs text-[#969696]">{COMPETENCY_LABELS[competency]}</p>
              <p className="border-l-4 border-[#c1f11d] pl-3 text-sm italic">&ldquo;{quote}&rdquo;</p>
            </div>
          ))
        ) : strengths.length > 0 ? (
          strengths.map(({ competency, item }, i) => (
            <div key={i} className="mb-2">
              <p className="text-xs text-[#969696]">{COMPETENCY_LABELS[competency]}</p>
              <EvidenceQuote item={item} showAtola={false} />
            </div>
          ))
        ) : (
          <p className="text-sm text-[#969696] italic">No demonstrated behaviour in the written material yet.</p>
        )}
      </section>

      <section>
        <h4 className="text-sm font-semibold text-[#141414] uppercase tracking-wider mb-2">By competency</h4>
        <div className="rounded-2xl border-2 border-[#d7d7d7] divide-y divide-[#d7d7d7]">
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
  const gaps = rating ? atolaGaps(rating) : [];
  const flags = rating?.flags ?? [];

  return (
    <div className="px-4 py-3 text-sm break-inside-avoid">
      <div className="flex items-center justify-between gap-3">
        <span className={`font-medium ${rating ? "text-[#141414]" : "text-[#969696]"}`}>{COMPETENCY_LABELS[competency]}</span>
        <span data-slot="evidence-state" data-state={state} className="text-xs text-[#5d5d5d] whitespace-nowrap">
          {EVIDENCE_STATE_LABELS[state]}
        </span>
      </div>

      {rating && !rating.reserved_for_humans && (
        <div data-slot="atola" className="mt-2 flex flex-wrap gap-1">
          {ATOLA_SEQUENCE.map((c) => {
            const present = rating.atola_present.includes(c);
            return (
              <span
                key={c}
                className={`px-1.5 py-0.5 rounded text-xs ${present ? "bg-[#c1f11d] text-[#141414]" : "border border-dashed border-[#969696] text-[#969696]"}`}
                title={present ? "Covered by the material" : "Missing: probe for this"}
              >
                {present ? "✓" : "?"} {ATOLA_LABELS[c]}
              </span>
            );
          })}
        </div>
      )}

      {preBrief?.probe ? (
        <div data-slot="probe" className="mt-2 space-y-1">
          <p><span className="text-[#969696]">Ask: </span>{preBrief.probe.paraphrase}</p>
          <p className="text-xs text-[#5d5d5d]"><span className="font-medium">Canonical probe: </span>{preBrief.probe.canonical}</p>
          <p className="text-xs text-[#5d5d5d]" data-slot="allowed-paraphrases">
            <span className="font-medium">Allowed wording: </span>{preBrief.probe.allowed_paraphrases.join(" / ")}
          </p>
        </div>
      ) : rating?.probe_question && (
        <p data-slot="probe" className="mt-2">
          <span className="text-[#969696]">Ask: </span>
          <span className="text-[#141414]">{rating.probe_question}</span>
          {gaps.length > 0 && !rating.reserved_for_humans && (
            <span className="text-xs text-[#969696]"> (first gap: {ATOLA_LABELS[gaps[0]]})</span>
          )}
        </p>
      )}

      {(preBrief?.discrepancy_alerts.length || flags.length > 0) && (
        <ul data-slot="flags" className="mt-2 space-y-1">
          {(preBrief?.discrepancy_alerts ?? flags).map((f, i) => (
            <li key={i} className="flex gap-2">
              <span className="shrink-0 mt-0.5 w-4 h-4 border border-[#141414] rounded-sm" aria-hidden />
              <span className="text-[#5d5d5d]">
                {f.quote && <q className="italic">{f.quote}</q>} {f.explanation}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
