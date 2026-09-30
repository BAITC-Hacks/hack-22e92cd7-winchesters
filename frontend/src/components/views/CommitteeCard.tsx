"use client";

import { useState } from "react";
import { competencyState, nineRows } from "@/lib/ledger";
import type { CandidateLedger, Competency, CompetencyRating, ScenarioResult } from "@/lib/types";
import { committeeLevel, type OverridesState } from "@/lib/useOverrides";
import { indicatorLabels, useRubric } from "@/lib/useRubric";
import { EvidenceQuote } from "../ledger/EvidenceQuote";
import { LevelChip } from "../ledger/LevelChip";
import { OverrideForm, OverrideHistory } from "../ledger/Override";
import { COMPETENCY_LABELS } from "../ledger/labels";

export interface CommitteeCardProps {
  ledger: CandidateLedger;
  /** The committee's override ledger (COM-01). Without it the card is read-only. */
  overrides?: OverridesState;
  /** The applicant's finished scenario, shown on its competency's row; weight zero. */
  scenario?: ScenarioResult | null;
}

// What the derivation rule ids mean, for the "About this assessment" section.
const RULES: [string, string][] = [
  ["R0", "No behaviour found for any indicator: No evidence."],
  ["R1", "Two or more indicators at High and none Weak: High."],
  ["R2", "At least one indicator Weak and none High: Weak."],
  ["R3", "Mixed or moderate evidence: Normal."],
];

/**
 * The committee's view of one applicant: one line per competency with its
 * BARS level, opening onto the verbatim quotes it rests on. Levels come from
 * the ledger as stored; this view never derives or averages one. Technical
 * provenance is kept, one click away, under "About this assessment".
 */
export function CommitteeCard({ ledger, overrides, scenario }: CommitteeCardProps) {
  const rubric = useRubric();
  // Only meaningful when the ledger was built under the rubric the server has now.
  const current = rubric?.version === ledger.rubric_version ? rubric : null;
  const drafts = new Set(current?.competencies.filter((c) => c.provisional).map((c) => c.competency) ?? []);
  const labels = indicatorLabels(rubric);
  const rows = nineRows(ledger);
  const aiRows = rows.filter(({ rating }) => !rating?.reserved_for_humans);
  const humanRows = rows.filter(({ rating }) => rating?.reserved_for_humans);

  return (
    <div className="space-y-5">
      <p className="text-sm text-ink-2">
        Each level rests on the applicant&apos;s own words: open a competency to read them.{" "}
        <span className="text-ink-3">&ldquo;No evidence&rdquo; means nothing was found, not a low rating.</span>
      </p>

      {overrides?.error && (
        <p className="rounded-2xl border border-danger/20 bg-danger-soft p-3 text-sm text-danger">Overrides unavailable: {overrides.error}</p>
      )}

      <div className="divide-y divide-line-soft rounded-2xl border border-line bg-white">
        {aiRows.map(({ competency, rating }) => (
          <CompetencyRow
            key={competency}
            competency={competency}
            rating={rating}
            overrides={overrides}
            labels={labels}
            scenario={scenario?.competency === competency ? scenario : null}
          />
        ))}
      </div>

      {humanRows.length > 0 && (
        <section>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-ink-2">Rated by people in the interview</h4>
          <div className="divide-y divide-line-soft rounded-2xl border border-line bg-white">
            {humanRows.map(({ competency, rating }) => (
              <CompetencyRow key={competency} competency={competency} rating={rating} overrides={overrides} labels={labels} />
            ))}
          </div>
        </section>
      )}

      <details className="group rounded-2xl bg-subtle px-4 py-3 text-xs text-ink-2">
        <summary className="cursor-pointer select-none font-semibold text-ink-2 hover:text-ink">About this assessment</summary>
        <div className="mt-3 space-y-3">
          {drafts.size > 0 && (
            <p data-slot="draft-rubric">
              <span className="font-medium text-ink">{drafts.size} of 9 scales are drafts</span> written from the published
              one-line descriptions; the Talent Craft BARS replace them when the extended methodology arrives.
            </p>
          )}
          <dl className="space-y-1">
            {RULES.map(([id, text]) => (
              <div key={id} className="flex gap-2">
                <dt className="font-mono text-ink">{id}</dt>
                <dd>{text}</dd>
              </div>
            ))}
          </dl>
          <Provenance ledger={ledger} rubricHash={current?.content_hash} />
        </div>
      </details>
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

/** The quote to preview on the closed row: behaviour shown first, then a claim. */
function previewQuote(rating?: CompetencyRating): string | null {
  const verified = rating?.indicators.flatMap((i) => i.evidence).filter((e) => e.verified) ?? [];
  return (verified.find((e) => e.status === "present") ?? verified[0])?.quote ?? null;
}

function CompetencyRow({
  competency,
  rating,
  overrides,
  labels,
  scenario = null,
}: {
  competency: Competency;
  rating?: CompetencyRating;
  overrides?: OverridesState;
  labels: Map<string, string>;
  scenario?: ScenarioResult | null;
}) {
  const [open, setOpen] = useState(false);
  const [overriding, setOverriding] = useState(false);
  const state = competencyState(rating);
  const aiLevel = rating?.level ?? null;
  const committee = committeeLevel(overrides?.history ?? null, competency);
  const history = overrides?.history?.filter((o) => o.competency === competency) ?? [];
  const canOverride = !!overrides?.history && !overrides.error;
  const preview = previewQuote(rating);
  const summary =
    state === "no_evidence"
      ? "Nothing found in the application yet."
      : state === "reserved"
        ? "No AI level: rated from the interview."
        : state === "not_in_ledger"
          ? "Not assessed yet."
          : null;

  return (
    <div data-competency={competency}>
      <button
        type="button"
        className="flex w-full items-center gap-4 px-5 py-4 text-left transition-colors hover:bg-subtle"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <div className="min-w-0 flex-1">
          <p className={`font-medium ${rating ? "text-ink" : "text-ink-3"}`}>{COMPETENCY_LABELS[competency]}</p>
          <p className="mt-0.5 truncate text-sm text-ink-3">{preview ? <q className="italic">{preview}</q> : summary}</p>
        </div>
        {scenario && (
          <span className="hidden items-center gap-1.5 text-xs text-ink-3 md:inline-flex" title="Observed in the scenario; weight 0, never changes the level">
            Scenario
            <LevelChip state={competencyState(scenario.rating)} small />
          </span>
        )}
        {/* The AI level is always shown; a committee override sits next to it, never in its place. */}
        <div className="flex shrink-0 items-center gap-2" data-slot="level-pair">
          {committee ? (
            <>
              <span className="hidden text-xs text-ink-3 sm:inline">AI</span>
              <LevelChip state={state} small />
              <span className="text-ink-3">→</span>
              <span className="rounded-full ring-2 ring-ink ring-offset-1" title="Committee level">
                <LevelChip state={committee} />
              </span>
            </>
          ) : (
            <LevelChip state={state} />
          )}
        </div>
        <svg
          className={`shrink-0 text-ink-3 transition-transform ${open ? "rotate-180" : ""}`}
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          aria-hidden
        >
          <path d="M4 6l4 4 4-4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {open && (
        <div className="space-y-4 px-5 pb-5">
          {rating && <Evidence rating={rating} labels={labels} />}

          {rating?.contrastive && state !== "reserved" && (
            <p data-slot="contrastive" className="rounded-xl bg-subtle px-3 py-2 text-sm text-ink-2">
              <span className="font-semibold text-ink">Next level: </span>
              {rating.contrastive}
            </p>
          )}

          {history.length > 0 && <OverrideHistory entries={history} reasonCodes={overrides?.reasonCodes ?? []} />}

          {canOverride && overrides && (overriding ? (
            <OverrideForm
              competency={competency}
              current={committee ?? aiLevel}
              aiLevel={aiLevel}
              reasonCodes={overrides.reasonCodes}
              onSubmit={overrides.create}
              onDone={() => setOverriding(false)}
            />
          ) : (
            <button
              type="button"
              onClick={() => setOverriding(true)}
              title="Record a committee level with a reason; the AI level stays visible"
              className="rounded-full border border-line px-4 py-1.5 text-sm font-semibold text-ink transition-colors hover:border-ink"
            >
              Change level
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/** The quotes, by behaviour, and which behaviours were not seen. */
function Evidence({ rating, labels }: { rating: CompetencyRating; labels: Map<string, string> }) {
  const shown = rating.indicators.filter((i) => i.evidence.length > 0);
  const missing = rating.indicators.filter((i) => i.evidence.length === 0);
  const capped = rating.indicators.filter((i) => i.capped_reason);
  const name = (id: string) => labels.get(id) ?? id;
  return (
    <div className="space-y-3">
      {shown.length > 0 && (
        <div>
          {shown.flatMap((indicator) =>
            indicator.evidence.map((item, i) => (
              <EvidenceQuote key={`${indicator.indicator_id}-${i}`} item={item} indicator={name(indicator.indicator_id)} />
            )),
          )}
        </div>
      )}
      {capped.map((indicator) => (
        <p key={indicator.indicator_id} className="text-xs text-ink-2">
          <span className="font-semibold text-ink">{name(indicator.indicator_id)}</span> kept at Normal: {indicator.capped_reason}
        </p>
      ))}
      {missing.length > 0 && !rating.reserved_for_humans && (
        <p className="text-xs text-ink-3">
          <span className="font-semibold text-ink-2">Not seen yet: </span>
          {missing.map((i) => name(i.indicator_id)).join(" · ")}
        </p>
      )}
    </div>
  );
}
