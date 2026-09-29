"use client";

import { useEffect, useMemo, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { AuditGroup, AuditState, Competency, FairnessAuditReport } from "@/lib/types";
import { COMPETENCY_LABELS } from "../ledger/labels";

// The audit keeps three written states, treats 0.8 as a review trigger, prints
// n beside every rate, and never turns competency levels into an average.

const DIMENSION_LABELS: Record<string, string> = {
  settlement_type: "Urban / rural",
  region: "Region",
  school_type: "School type",
  application_language: "Application language",
  foundation_eligible: "Foundation eligible",
  gender: "Gender",
  settlement_x_language: "Urban/rural × language",
};

const LANGUAGE_LABELS: Record<string, string> = { kk: "Kazakh", ru: "Russian", en: "English", mixed: "Mixed" };

function groupLabel(dimension: string, group: string): string {
  if (dimension === "application_language") return LANGUAGE_LABELS[group] ?? group;
  if (dimension === "settlement_x_language") {
    const [settlement, language] = group.split(" × ");
    return `${settlement} × ${LANGUAGE_LABELS[language] ?? language}`;
  }
  return group.replace(/_/g, " ");
}

const STATE_TEXT: Record<AuditState, string> = {
  ok: "Looks fine",
  review_needed: "Check this",
  not_enough_data: "Too few to tell",
};

const STATE_BADGE: Record<AuditState, string> = {
  ok: "bg-[#eef9d0] text-accent-ink border-[#9cc20f]",
  review_needed: "bg-amber-50 text-amber-800 border-amber-400",
  not_enough_data: "bg-white text-ink-2 border-dashed border-ink-3",
};



const percent = (v: number) => `${Math.round(v * 100)}%`;

export function AttributeAudit() {
  const [report, setReport] = useState<FairnessAuditReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [competency, setCompetency] = useState<Competency | null>(null);
  const [dimension, setDimension] = useState("settlement_x_language");

  useEffect(() => {
    api.fairness
      .audit("synthetic")
      .then((r) => {
        setReport(r);
        const planted = r.synthetic?.planted_effects[0]?.competency as Competency | undefined;
        setCompetency(planted && r.competencies.includes(planted) ? planted : r.competencies[0]);
      })
      .catch((e) =>
        setError(e instanceof ApiError && e.status === 403 ? "The attribute audit is for committee and admin only." : String(e.message ?? e)),
      );
  }, []);

  const cell = useMemo(
    () =>
      report?.dimensions
        .find((d) => d.dimension === dimension)
        ?.competencies.find((c) => c.competency === competency),
    [report, dimension, competency],
  );
  const undeclared = report?.dimensions.find((d) => d.dimension === dimension)?.undeclared ?? 0;

  if (error) return <p className="text-sm text-ink-2">{error}</p>;
  if (!report || !competency) return <p className="text-sm text-ink-3">Loading the attribute audit…</p>;

  const threshold = report.method.review_threshold;

  return (
    <section className="space-y-4">
      <div className="rounded-2xl bg-subtle px-4 py-3 text-sm text-ink-2">
        <p className="font-semibold text-ink">How to read this</p>
        <ol className="mt-1.5 list-decimal space-y-0.5 pl-5">
          <li>Pick a competency and what to compare by, for example urban and rural applicants.</li>
          <li>Each row is a group of applicants, and how often they were rated <strong>High</strong>.</li>
          <li>
            That rate is compared with the best group. Below {Math.round(threshold * 100)}% of the best group&apos;s rate
            means the committee should look closer. It is a prompt to check, not proof of bias.
          </li>
        </ol>
      </div>

      {report.synthetic && (
        <div role="note" data-slot="synthetic-notice" className="rounded-xl border border-amber-400 bg-amber-50 px-4 py-2.5 text-sm text-amber-900">
          <span className="font-semibold">Sample data, not real applicants.</span> {report.synthetic.size} generated profiles
          show how the check works. A gap was planted on purpose so you can see what a warning looks like
          {report.synthetic.planted_effects[0] &&
            ` (${COMPETENCY_LABELS[report.synthetic.planted_effects[0].competency as Competency] ?? report.synthetic.planted_effects[0].competency}, ${groupLabel("settlement_x_language", report.synthetic.planted_effects[0].group)})`}
          .
        </div>
      )}

      <div className="flex flex-col gap-3 md:flex-row md:items-end">
        <label className="flex flex-col gap-1 text-xs font-semibold text-ink-2">
          Competency
          <select
            value={competency}
            onChange={(e) => setCompetency(e.target.value as Competency)}
            className="rounded-xl border border-line bg-white px-3 py-2 text-sm font-normal text-ink outline-none focus:border-ink"
          >
            {report.competencies.map((c) => (
              <option key={c} value={c}>
                {COMPETENCY_LABELS[c]}
              </option>
            ))}
          </select>
        </label>
        <div className="flex flex-col gap-1">
          <span className="text-xs font-semibold text-ink-2">Compare by</span>
          <div className="flex flex-wrap gap-1.5" role="tablist" aria-label="Attribute">
            {report.dimensions.map((d) => (
              <button
                key={d.dimension}
                type="button"
                role="tab"
                aria-selected={d.dimension === dimension}
                onClick={() => setDimension(d.dimension)}
                className={`rounded-full border px-3 py-1.5 text-xs ${
                  d.dimension === dimension ? "border-ink bg-ink text-white" : "border-line bg-white text-ink-2 hover:border-ink-3"
                }`}
              >
                {DIMENSION_LABELS[d.dimension] ?? d.dimension}
              </button>
            ))}
          </div>
        </div>
      </div>

      {!cell || cell.groups.length === 0 ? (
        <p className="text-sm text-ink-2">No applicant has both a declared value and a level here yet.</p>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-line">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b border-line bg-subtle text-left text-xs uppercase tracking-wider text-ink-3">
                <th className="px-4 py-2.5 font-medium">Group</th>
                <th className="px-3 py-2.5 text-right font-medium">Applicants</th>
                <th className="px-3 py-2.5 font-medium">Rated High</th>
                <th className="px-3 py-2.5 font-medium">Compared with best group</th>
                <th className="px-4 py-2.5 font-medium">Result</th>
              </tr>
            </thead>
            <tbody>
              {cell.groups.map((g) => (
                <GroupRow key={g.group} g={g} label={groupLabel(dimension, g.group)} threshold={threshold} />
              ))}
            </tbody>
          </table>
        </div>
      )}
      {undeclared > 0 && (
        <p className="text-xs text-ink-3">
          {undeclared} applicant{undeclared === 1 ? "" : "s"} did not declare this and {undeclared === 1 ? "is" : "are"} not in any group.
        </p>
      )}

    </section>
  );
}

function GroupRow({ g, label, threshold }: { g: AuditGroup; label: string; threshold: number }) {
  const dimmed = g.state === "not_enough_data";
  const reason =
    g.state === "not_enough_data"
      ? "Too few applicants to compare"
      : g.review_reason === "below_threshold"
        ? `Gets High less than ${Math.round(threshold * 100)}% as often as the best group`
        : g.review_reason
          ? "Too uncertain to rule out a gap"
          : null;
  return (
    <tr data-state={g.state} className={`border-b border-line-soft last:border-b-0 ${dimmed ? "text-ink-3" : "text-ink"}`}>
      <td className="px-4 py-3 capitalize">
        {label}
        {g.is_reference && <span className="ml-2 rounded bg-muted px-1.5 py-px text-[10px] uppercase tracking-wider text-ink-2">best group</span>}
      </td>
      <td className="px-3 py-3 text-right font-mono">{g.n}</td>
      <td className="px-3 py-3">
        <div className="flex items-center gap-2">
          <div className="h-2 w-24 overflow-hidden rounded-full bg-muted">
            <div className="h-full rounded-full bg-accent" style={{ width: percent(Math.min(g.high_rate, 1)) }} />
          </div>
          <span className="font-mono text-xs">{percent(g.high_rate)}</span>
        </div>
      </td>
      <td className="px-3 py-3 text-xs">
        {g.is_reference ? (
          <span className="text-ink-3">reference</span>
        ) : g.impact_ratio === null ? (
          <span className="text-ink-3">—</span>
        ) : (
          <span className={g.state === "review_needed" ? "font-semibold" : ""}>
            {`${percent(g.impact_ratio)} of the best group's rate`}
          </span>
        )}
      </td>
      <td className="px-4 py-3">
        <span className={`inline-block whitespace-nowrap rounded-full border px-2.5 py-0.5 text-xs ${STATE_BADGE[g.state]}`}>{STATE_TEXT[g.state]}</span>
        {reason && g.state !== "ok" && <span className="mt-0.5 block text-[11px] text-ink-3">{reason}</span>}
      </td>
    </tr>
  );
}
