"use client";

import { competencyState } from "@/lib/ledger";
import type { ScenarioResult } from "@/lib/types";
import { indicatorLabels, useRubric } from "@/lib/useRubric";
import { EvidenceQuote } from "../ledger/EvidenceQuote";
import { LevelChip } from "../ledger/LevelChip";
import { COMPETENCY_LABELS } from "../ledger/labels";
import { ProvisionalChip, SimulationLabel, Transcript } from "../simulation/SimulationLabels";

const LANGUAGE_NAMES = { en: "English", ru: "Russian", kk: "Kazakh" } as const;
const PARTNER = { en: "Conversation partner", ru: "Собеседник", kk: "Әңгімелесуші" } as const;

/**
 * The applicant's scenario, rated on the rubric from their own replies. Shown
 * next to the written evidence, never merged into it: weight zero.
 */
export function ScenarioPanel({ result }: { result: ScenarioResult | null }) {
  const labels = indicatorLabels(useRubric());
  if (!result) {
    return (
      <section className="rounded-2xl border border-line bg-white p-5">
        <h3 className="font-semibold text-ink">Scenario</h3>
        <p className="mt-1 text-sm text-ink-2">No scenario finished by this applicant yet.</p>
      </section>
    );
  }
  const quotes = result.rating.indicators.flatMap((indicator) =>
    indicator.evidence.map((item) => ({ item, indicator: labels.get(indicator.indicator_id) ?? indicator.indicator_id })),
  );
  const title = result.scenario.text?.en?.title ?? result.scenario.id;
  return (
    <section className="space-y-4 rounded-2xl border border-line bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-ink">Scenario: {title}</h3>
          <p className="mt-0.5 text-sm text-ink-2">
            {COMPETENCY_LABELS[result.competency]} · answered in {LANGUAGE_NAMES[result.language]}
          </p>
        </div>
        <LevelChip state={competencyState(result.rating)} />
      </div>
      <SimulationLabel demo={result.source === "demo"} />
      {quotes.length > 0 ? (
        <div>
          {quotes.map(({ item, indicator }, i) => (
            <EvidenceQuote key={i} item={item} indicator={indicator} showAtola />
          ))}
        </div>
      ) : (
        <p className="text-sm text-ink-2">Nothing in the replies spoke to this competency.</p>
      )}
      <details className="text-sm">
        <summary className="cursor-pointer select-none text-xs font-semibold text-ink-2 hover:text-ink">Full conversation</summary>
        <div className="mt-3 space-y-3">
          <ProvisionalChip scenario={result.scenario} />
          <Transcript messages={result.messages} partnerLabel={PARTNER[result.language]} />
        </div>
      </details>
    </section>
  );
}
