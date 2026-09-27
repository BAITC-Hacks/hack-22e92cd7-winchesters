"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { competencyState, nineRows } from "@/lib/ledger";
import type { CandidateLedger, Competency, CompetencyRating, IndicatorRating, RubricStatus } from "@/lib/types";
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
  const [rubric, setRubric] = useState<RubricStatus | null>(null);
  useEffect(() => {
    api.ledger.rubric().then(setRubric).catch(() => setRubric(null));
  }, []);
  // Only meaningful when the ledger was built under the rubric the server has now.
  const current = rubric?.version === ledger.rubric_version ? rubric : null;
  const drafts = new Set(current?.competencies.filter((c) => c.provisional).map((c) => c.competency) ?? []);

  return (
    <div className="space-y-4">
      <div className="rounded-2xl bg-subtle px-4 py-3 space-y-2">
        <Provenance ledger={ledger} rubricHash={current?.content_hash} />
        {drafts.size > 0 && (
          <p data-slot="draft-rubric" className="text-xs text-ink-2">
            <span className="font-medium text-ink">{drafts.size} of 9 scales are drafts</span> written from the published
            one-line descriptions; the Talent Craft BARS replace them when the extended methodology arrives.
          </p>
        )}
      </div>
      {overrides?.error && (
        <p className="p-3 bg-red-500/10 text-red-600 rounded-2xl text-sm border border-red-500/20">
          Overrides unavailable: {overrides.error}
        </p>
      )}
      <div className="rounded-2xl border-2 border-line divide-y divide-line-soft bg-white">
        {nineRows(ledger).map(({ competency, rating }) => (
          <CompetencyRow key={competency} competency={competency} rating={rating} overrides={overrides} draft={drafts.has(competency)} />
        ))}
      </div>
    </div>
  );
}

function Provenance({ ledger, rubricHash }: { ledger: CandidateLedger; rubricHash?: string }) {
  const items: [string, string][] = [
    ["Applicant", ledger.applicant_ref],
    ["Rubric", rubricHash ? `${ledger.rubric_version} · sha256:${rubricHash.slice(0, 12)}` : ledger.rubric_version],
    ["Prompt", ledger.prompt_version],
    ["Extract", ledger.model_extract],
    ["Judge", ledger.model_judge],
    ["Schema", ledger.schema_version],
  ];
  return (
    <dl data-slot="provenance" className="flex flex-wrap gap-x-5 gap-y-1 text-[11px] text-ink-3">
      {items.map(([k, v]) => (
        <div key={k} className="flex gap-1">
          <dt>{k}:</dt>
          <dd className="font-mono text-ink-2">{v || "—"}</dd>
        </div>
      ))}
    </dl>
  );
}

function CompetencyRow({
  competency,
  rating,
  overrides,
  draft,
}: {
  competency: Competency;
  rating?: CompetencyRating;
  overrides?: OverridesState;
  draft: boolean;
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
          <span className={`text-base font-medium ${rating ? "text-ink" : "text-ink-3"}`}>
            {COMPETENCY_LABELS[competency]}
          </span>
          {rating?.rule_applied && (
            <span className="text-xs font-mono text-ink-3" title="Derivation rule that fired">
              {rating.rule_applied}
            </span>
          )}
          {draft && (
            <span
              className="rounded-full border border-dashed border-ink-3 px-2 py-0.5 text-[10px] uppercase tracking-wide text-ink-2"
              title="Scale drafted by the team; replaced by the Talent Craft BARS (LED-13)"
            >
              Draft scale
            </span>
          )}
          {expandable && <span className="text-ink-3 text-sm">{open ? "−" : "+"}</span>}
        </button>
        {/* The AI level is always shown; a committee override sits next to it, never in its place. */}
        <div className="flex items-center gap-2" data-slot="level-pair">
          {aiLevel && <span className="text-xs text-ink-3">AI</span>}
          <LevelChip state={state} />
          {committee && (
            <>
              <span className="text-ink-3">→</span>
              <span className="text-xs text-ink-3">Committee</span>
              <span className="rounded-full ring-2 ring-offset-1 ring-ink">
                <LevelChip state={committee} />
              </span>
            </>
          )}
          {canOverride && !overriding && (
            <button
              className="ml-1 rounded-full px-2.5 py-1 text-xs font-medium text-ink-2 hover:bg-muted hover:text-ink transition-colors"
              onClick={() => setOverriding(true)}
              title="Record a committee level with a reason; the AI level stays visible"
            >
              Override
            </button>
          )}
        </div>
      </div>

      {state === "no_evidence" && (
        <p className="mt-1 text-sm text-ink-2">
          No behaviour for this competency was found in the material. This is not a low rating.
        </p>
      )}
      {state === "reserved" && (
        <p className="mt-1 text-sm text-ink-2">No AI level: the methodology owner rates this from the interview.</p>
      )}
      {rating && <ContrastiveHint text={rating.contrastive} />}

      {history.length > 0 && <OverrideHistory entries={history} reasonCodes={overrides?.reasonCodes ?? []} />}
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
            <p className="text-xs text-ink-3">
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
    <div className="rounded-xl bg-subtle p-3 text-sm">
      <div className="flex items-center gap-2 mb-2 flex-wrap">
        <IndicatorId id={indicator.indicator_id} />
        <LevelChip state={indicator.observed_level} small />
        {indicator.capped_reason && (
          <span className="text-xs text-ink bg-muted rounded px-1.5 py-0.5" title={indicator.capped_reason}>
            Capped: {indicator.capped_reason}
          </span>
        )}
      </div>
      {indicator.evidence.length > 0 ? (
        indicator.evidence.map((item, i) => <EvidenceQuote key={i} item={item} />)
      ) : (
        <p className="text-ink-3 italic">No evidence for this indicator.</p>
      )}
      {indicator.note && <p className="mt-2 text-ink-2">{indicator.note}</p>}
    </div>
  );
}
