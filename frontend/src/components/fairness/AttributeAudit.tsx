"use client";

import { useEffect, useMemo, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { AuditGroup, AuditState, Competency, FairnessAuditReport, Level } from "@/lib/types";
import { COMPETENCY_LABELS, STATE_LABELS } from "../ledger/labels";

// Placeholder visuals until FAIR-03 delivers the fairness visual language. What
// must survive the redesign: three states with words, not colour alone; one
// line at 0.8 that reads as "review", not "fail"; n printed next to every rate;
// and no level ever turned into an average.

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
  ok: "OK",
  review_needed: "Review needed",
  not_enough_data: "Not enough data",
};

const STATE_BADGE: Record<AuditState, string> = {
  ok: "bg-[#eef9d0] text-[#3d4f00] border-[#9cc20f]",
  review_needed: "bg-amber-50 text-amber-800 border-amber-400",
  not_enough_data: "bg-white text-[#5d5d5d] border-dashed border-[#969696]",
};

const STATE_MARK: Record<AuditState, string> = {
  ok: "#6f8c00",
  review_needed: "#b45309",
  not_enough_data: "#969696",
};

// Same fills as LevelChip, so a segment reads as the chip it counts.
const LEVEL_ORDER: Level[] = ["high", "normal", "weak", "no_evidence"];
const LEVEL_FILL: Record<Level, React.CSSProperties> = {
  high: { background: "#c1f11d" },
  normal: { background: "#d7d6d6" },
  weak: { background: "#5d5d5d" },
  no_evidence: { background: "repeating-linear-gradient(45deg, #fff 0 3px, #bbb 3px 5px)" },
};

const AXIS_MAX = 2;
const pct = (v: number) => `${(Math.min(Math.max(v, 0), AXIS_MAX) / AXIS_MAX) * 100}%`;
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

  if (error) return <p className="text-sm text-[#5d5d5d]">{error}</p>;
  if (!report || !competency) return <p className="text-sm text-[#969696]">Loading the attribute audit…</p>;

  const threshold = report.method.review_threshold;

  return (
    <section className="space-y-4">
      <div>
        <h4 className="text-sm font-semibold text-[#141414] uppercase tracking-wider mb-1">
          Attribute-grouped audit
        </h4>
        <p className="text-xs text-[#5d5d5d]">
          Share of each group rated <strong>High</strong>, against the best group with enough data. Levels are counted,
          never averaged. {threshold} is a line for human review, not a pass mark.
        </p>
      </div>

      {report.synthetic && (
        <div
          role="note"
          data-slot="synthetic-notice"
          className="rounded-xl border-2 border-amber-400 bg-amber-50 px-4 py-3 text-sm text-amber-900"
        >
          <p className="font-semibold uppercase tracking-wider text-xs mb-1">
            Synthetic data — demonstrates the method, not evidence
          </p>
          <p>
            {report.synthetic.size} generated profiles (seed {report.synthetic.cohort_seed}), no real applicants and no
            model calls. Real levels arrive with LED-11.
          </p>
          {report.synthetic.planted_effects.map((p) => (
            <p key={p.competency + p.group} className="mt-1 text-xs">
              Planted on purpose so the review state is visible — {COMPETENCY_LABELS[p.competency as Competency] ?? p.competency},{" "}
              {groupLabel("settlement_x_language", p.group)}: {p.effect}.
            </p>
          ))}
        </div>
      )}

      <div className="flex flex-wrap gap-3 items-end">
        <label className="text-xs text-[#5d5d5d] flex flex-col gap-1">
          Competency
          <select
            value={competency}
            onChange={(e) => setCompetency(e.target.value as Competency)}
            className="border border-[#d7d7d7] rounded-lg px-2 py-1.5 text-sm text-[#141414] bg-white"
          >
            {report.competencies.map((c) => (
              <option key={c} value={c}>
                {COMPETENCY_LABELS[c]}
              </option>
            ))}
          </select>
        </label>
        <div className="flex flex-wrap gap-1.5" role="tablist" aria-label="Attribute">
          {report.dimensions.map((d) => (
            <button
              key={d.dimension}
              role="tab"
              aria-selected={d.dimension === dimension}
              onClick={() => setDimension(d.dimension)}
              className={`px-3 py-1.5 rounded-full text-xs border ${
                d.dimension === dimension
                  ? "bg-[#141414] text-white border-[#141414]"
                  : "bg-white text-[#5d5d5d] border-[#d7d7d7] hover:border-[#969696]"
              }`}
            >
              {DIMENSION_LABELS[d.dimension] ?? d.dimension}
            </button>
          ))}
        </div>
      </div>

      {!cell || cell.groups.length === 0 ? (
        <p className="text-sm text-[#5d5d5d]">No applicant has both a declared value and a level here yet.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[760px]">
            <thead>
              <tr className="text-left text-xs text-[#969696] uppercase tracking-wider border-b border-[#eee]">
                <th className="py-2 pr-3 font-medium">Group</th>
                <th className="py-2 pr-3 font-medium text-right">n</th>
                <th className="py-2 pr-3 font-medium w-40">Levels</th>
                <th className="py-2 pr-3 font-medium text-right">High</th>
                <th className="py-2 pr-3 font-medium text-right">No evidence</th>
                <th className="py-2 pr-3 font-medium w-64">Impact ratio, 95% CI</th>
                <th className="py-2 font-medium">State</th>
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

      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-[#5d5d5d]">
        {LEVEL_ORDER.map((level) => (
          <span key={level} className="flex items-center gap-1.5">
            <span className="inline-block w-3 h-3 rounded-sm border border-[#d7d7d7]" style={LEVEL_FILL[level]} />
            {STATE_LABELS[level]}
          </span>
        ))}
        {undeclared > 0 && <span>· {undeclared} applicant{undeclared === 1 ? "" : "s"} did not declare this</span>}
      </div>

      <p className="text-xs text-[#969696] leading-relaxed">
        Not enough data: n &lt; {report.method.min_group_n} or under {percent(report.method.min_group_share)} of the pool
        (rates still shown). Review needed: ratio below {threshold}, or its interval reaches below it. Interval:{" "}
        {report.method.interval}, seed {report.method.bootstrap_seed}. Input sha256{" "}
        <code className="font-mono">{report.input_hash.slice(0, 16)}…</code>. Same numbers:{" "}
        <code className="font-mono">python -m backend.scoring.fairness_audit</code>.
      </p>
    </section>
  );
}

function GroupRow({ g, label, threshold }: { g: AuditGroup; label: string; threshold: number }) {
  const dimmed = g.state === "not_enough_data";
  return (
    <tr data-state={g.state} className={`border-b border-[#f3f3f3] ${dimmed ? "text-[#969696]" : "text-[#141414]"}`}>
      <td className="py-2 pr-3 capitalize">
        {label}
        {g.is_reference && <span className="ml-1.5 text-[10px] uppercase tracking-wider text-[#969696]">reference</span>}
      </td>
      <td className="py-2 pr-3 text-right font-mono">{g.n}</td>
      <td className="py-2 pr-3">
        <div
          className="flex h-3 w-36 rounded-sm overflow-hidden border border-[#e5e5e5]"
          title={LEVEL_ORDER.map((l) => `${STATE_LABELS[l]}: ${g.levels[l]}`).join(" · ")}
        >
          {LEVEL_ORDER.map((l) =>
            g.levels[l] > 0 ? <span key={l} style={{ ...LEVEL_FILL[l], width: `${(g.levels[l] / g.n) * 100}%` }} /> : null,
          )}
        </div>
      </td>
      <td className="py-2 pr-3 text-right font-mono">{percent(g.high_rate)}</td>
      <td className="py-2 pr-3 text-right font-mono">{percent(g.no_evidence_rate)}</td>
      <td className="py-2 pr-3">
        <RatioBar g={g} threshold={threshold} />
      </td>
      <td className="py-2">
        <span className={`inline-block border rounded-full px-2 py-0.5 text-xs whitespace-nowrap ${STATE_BADGE[g.state]}`}>
          {STATE_TEXT[g.state]}
        </span>
        {g.review_reason && (
          <span className="block text-[10px] text-[#969696] mt-0.5">
            {g.review_reason === "below_threshold" ? `ratio below ${threshold}` : `interval crosses ${threshold}`}
          </span>
        )}
      </td>
    </tr>
  );
}

function RatioBar({ g, threshold }: { g: AuditGroup; threshold: number }) {
  if (g.impact_ratio === null) return <span className="text-xs text-[#969696]">—</span>;
  const color = STATE_MARK[g.state];
  const ci = g.ci_low !== null && g.ci_high !== null ? `${g.ci_low.toFixed(2)}–${g.ci_high.toFixed(2)}` : "—";
  return (
    <div className="flex items-center gap-2">
      <div className="relative h-4 w-36 shrink-0" aria-hidden>
        <div className="absolute inset-y-[7px] inset-x-0 bg-[#f0f0f0] rounded" />
        <div className="absolute inset-y-0 w-px bg-[#c9c9c9]" style={{ left: pct(1) }} />
        <div className="absolute inset-y-[-2px] border-l-2 border-dashed border-amber-500" style={{ left: pct(threshold) }} />
        {g.ci_low !== null && g.ci_high !== null && (
          <div
            className="absolute top-[7px] h-[2px]"
            style={{ left: pct(g.ci_low), width: `calc(${pct(g.ci_high)} - ${pct(g.ci_low)})`, background: color }}
          />
        )}
        <div
          className="absolute top-[3px] h-2.5 w-2.5 -ml-[5px] rounded-full border-2 border-white"
          style={{ left: pct(g.impact_ratio), background: color }}
        />
      </div>
      <span className="font-mono text-xs whitespace-nowrap">
        {g.impact_ratio.toFixed(2)} <span className="text-[#969696]">[{ci}]</span>
      </span>
    </div>
  );
}
