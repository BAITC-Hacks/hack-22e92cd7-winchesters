"use client";

import { useState } from "react";
import { competencyState, nineRows } from "@/lib/ledger";
import type { CandidateLedger, Competency, CompetencyRating, IndicatorRating } from "@/lib/types";
import { committeeLevel, type OverridesState } from "@/lib/useOverrides";
import { ContrastiveHint } from "../ledger/ContrastiveHint";
import { EvidenceQuote, IndicatorId } from "../ledger/EvidenceQuote";
import { LevelChip } from "../ledger/LevelChip";
import { OverrideForm, OverrideHistory } from "../ledger/Override";
import { COMPETENCY_LABELS } from "../ledger/labels";

export interface CommitteeCardProps {
  ledger: CandidateLedger;
  /** The committee's override ledger (COM-01). Without it the card is read-only. */
  overrides?: OverridesState;
}

/**
 * The committee's view of one applicant: nine competencies, each a BARS level
 * that decomposes into indicators and verbatim quotes. Levels come from the
 * ledger as stored; this view never derives or averages one.
 */
export function CommitteeCard({ ledger, overrides }: CommitteeCardProps) {
  return (
    <div className="space-y-4">
      <Provenance ledger={ledger} />
      {overrides?.error && (
        <p className="p-3 bg-red-500/10 text-red-600 rounded-2xl text-sm border border-red-500/20">
          Overrides unavailable: {overrides.error}
        </p>
      )}
      <div className="rounded-2xl border-2 border-[#d7d7d7] divide-y divide-[#d7d7d7]">
        {nineRows(ledger).map(({ competency, rating }) => (
          <CompetencyRow key={competency} competency={competency} rating={rating} overrides={overrides} />
        ))}
      </div>
    </div>
  );
}

function Provenance({ ledger }: { ledger: CandidateLedger }) {
  const items: [string, string][] = [
    ["Applicant", ledger.applicant_ref],
    ["Rubric", ledger.rubric_version],
    ["Prompt", ledger.prompt_version],
    ["Extract", ledger.model_extract],
    ["Judge", ledger.model_judge],
    ["Schema", ledger.schema_version],
  ];
  return (
    <dl data-slot="provenance" className="flex flex-wrap gap-x-5 gap-y-1 text-xs text-[#969696]">
      {items.map(([k, v]) => (
        <div key={k} className="flex gap-1">
          <dt>{k}:</dt>
          <dd className="font-mono text-[#5d5d5d]">{v || "—"}</dd>
        </div>
      ))}
    </dl>
  );
}

function CompetencyRow({
  competency,
  rating,
  overrides,
}: {
  competency: Competency;
  rating?: CompetencyRating;
  overrides?: OverridesState;
}) {
  const [open, setOpen] = useState(false);
  const [overriding, setOverriding] = useState(false);
  const state = competencyState(rating);
  const expandable = !!rating && rating.indicators.length > 0;
  const aiLevel = rating?.level ?? null;
  const committee = committeeLevel(overrides?.history ?? null, competency);
  const history = overrides?.history?.filter((o) => o.competency === competency) ?? [];
  const canOverride = !!overrides?.history && !overrides.error;

  return (
    <div className="px-5 py-4" data-competency={competency}>
      <div className="flex items-start gap-3">
        <button
          className="flex-1 text-left flex items-center gap-3 disabled:cursor-default"
          onClick={() => setOpen(!open)}
          disabled={!expandable}
          aria-expanded={open}
        >
          <span className={`text-base font-medium ${rating ? "text-[#141414]" : "text-[#969696]"}`}>
            {COMPETENCY_LABELS[competency]}
          </span>
          {rating?.rule_applied && (
            <span className="text-xs font-mono text-[#969696]" title="Derivation rule that fired">
              {rating.rule_applied}
            </span>
          )}
          {expandable && <span className="text-gray-400 text-sm">{open ? "−" : "+"}</span>}
        </button>
        {/* The AI level is always shown; a committee override sits next to it, never in its place. */}
        <div className="flex items-center gap-2" data-slot="level-pair">
          {aiLevel && <span className="text-xs text-[#969696]">AI</span>}
          <LevelChip state={state} />
          {committee && (
            <>
              <span className="text-[#969696]">→</span>
              <span className="text-xs text-[#969696]">Committee</span>
              <span className="rounded-full ring-2 ring-offset-1 ring-[#141414]">
                <LevelChip state={committee} />
              </span>
            </>
          )}
        </div>
      </div>

      {state === "no_evidence" && (
        <p className="mt-1 text-sm text-[#5d5d5d]">
          No behaviour for this competency was found in the material. This is not a low rating.
        </p>
      )}
      {state === "reserved" && (
        <p className="mt-1 text-sm text-[#5d5d5d]">No AI level: the methodology owner rates this from the interview.</p>
      )}
      {rating && <ContrastiveHint text={rating.contrastive} />}

      {history.length > 0 && <OverrideHistory entries={history} reasonCodes={overrides?.reasonCodes ?? []} />}
      {canOverride && !overriding && (
        <button
          className="mt-2 text-xs font-medium text-[#5d5d5d] underline underline-offset-2 hover:text-[#141414]"
          onClick={() => setOverriding(true)}
        >
          Override level
        </button>
      )}
      {canOverride && overriding && overrides && (
        <OverrideForm
          competency={competency}
          current={committee ?? aiLevel}
          aiLevel={aiLevel}
          reasonCodes={overrides.reasonCodes}
          onSubmit={overrides.create}
          onDone={() => setOverriding(false)}
        />
      )}

      {open && rating && (
        <div className="mt-3 space-y-3">
          {rating.indicators.map((ind) => (
            <IndicatorRow key={ind.indicator_id} indicator={ind} />
          ))}
          {rating.flags.length > 0 && (
            <p className="text-xs text-[#969696]">
              {rating.flags.length} attention flag{rating.flags.length === 1 ? "" : "s"} routed to the interviewer brief.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function IndicatorRow({ indicator }: { indicator: IndicatorRating }) {
  return (
    <div className="rounded-xl bg-[#f5f5f5] p-3 text-sm">
      <div className="flex items-center gap-2 mb-2 flex-wrap">
        <IndicatorId id={indicator.indicator_id} />
        <LevelChip state={indicator.observed_level} small />
        {indicator.capped_reason && (
          <span className="text-xs text-[#141414] bg-[#eae9e9] rounded px-1.5 py-0.5" title={indicator.capped_reason}>
            Capped: {indicator.capped_reason}
          </span>
        )}
      </div>
      {indicator.evidence.length > 0 ? (
        indicator.evidence.map((item, i) => <EvidenceQuote key={i} item={item} />)
      ) : (
        <p className="text-[#969696] italic">No evidence for this indicator.</p>
      )}
      {indicator.note && <p className="mt-2 text-[#5d5d5d]">{indicator.note}</p>}
    </div>
  );
}
