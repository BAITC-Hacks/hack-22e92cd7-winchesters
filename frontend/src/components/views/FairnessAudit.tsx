"use client";

import { useMemo } from "react";
import { groupOf, groupsFor, scoreOf, type Scorer } from "@/lib/dashboard";
import { ledgerStats, type CompetencyState } from "@/lib/ledger";
import type { CandidateLedger, RankedCandidate } from "@/lib/types";
import { CollapsiblePanel } from "../ui/CollapsiblePanel";
import { AttributeAudit } from "../fairness/AttributeAudit";
import { LevelChip } from "../ledger/LevelChip";

export interface FairnessAuditProps {
  ranked: RankedCandidate[];
  scorer: Scorer;
  ledgers: CandidateLedger[];
}

/**
 * Cohort-level checks. Two parts with very different standing:
 *
 * - Ledger health: how often the pipeline abstained, capped or found nothing.
 *   Counts only; a level is never averaged.
 * - The attribute-grouped audit (FAIR-07): impact ratios by declared background.
 * - The legacy table by score group. It cannot detect bias; task FAIR-02 removes it.
 */
export function FairnessAudit({ ranked, scorer, ledgers }: FairnessAuditProps) {
  return (
    <CollapsiblePanel icon="/assets/Scales.svg" title="Fairness Audit">
      <div className="space-y-6">
        <div data-slot="attribute-audit">
          <AttributeAudit />
        </div>
        <LedgerHealth ledgers={ledgers} />
        <LegacyGroupTable ranked={ranked} scorer={scorer} />
      </div>
    </CollapsiblePanel>
  );
}

const STATE_ORDER: CompetencyState[] = ["high", "normal", "weak", "no_evidence", "reserved", "not_in_ledger"];

function LedgerHealth({ ledgers }: { ledgers: CandidateLedger[] }) {
  const s = useMemo(() => ledgerStats(ledgers), [ledgers]);
  const facts: [string, number, string][] = [
    ["Indicators without verified evidence", s.indicatorsWithoutEvidence, `of ${s.indicators}`],
    ["Indicators capped (claimed, not shown)", s.cappedIndicators, `of ${s.indicators}`],
    ["Quotes that failed verification", s.unverifiedItems, `of ${s.evidenceItems}`],
    ["Attention flags for interviewers", s.flags, ""],
  ];
  return (
    <section>
      <h4 className="text-sm font-semibold text-[#141414] uppercase tracking-wider mb-1">Ledger health</h4>
      <p className="text-xs text-[#969696] mb-3">
        {s.ledgers} ledger{s.ledgers === 1 ? "" : "s"} × 9 competencies. Until LED-11 this is the LED-03 fixture.
      </p>
      <div className="flex flex-wrap gap-3 mb-4">
        {STATE_ORDER.map((state) => (
          <div key={state} className="flex items-center gap-2">
            <LevelChip state={state} small />
            <span className="font-mono text-sm text-[#141414]">{s.competencyStates[state]}</span>
          </div>
        ))}
      </div>
      <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-1 text-sm">
        {facts.map(([label, value, of]) => (
          <div key={label} className="flex justify-between border-b border-[#eee] py-1">
            <dt className="text-[#5d5d5d]">{label}</dt>
            <dd className="font-mono text-[#141414]">
              {value} <span className="text-[#969696]">{of}</span>
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function LegacyGroupTable({ ranked, scorer }: { ranked: RankedCandidate[]; scorer: Scorer }) {
  const auditStats = useMemo(() => {
    const groups: Record<string, { scores: number[]; growth: number[]; leadership: number[] }> = {};

    for (const r of ranked) {
      const key = groupOf(r, scorer);
      if (!key) continue;
      const score = scoreOf(r);
      const growthDim = score?.dimensions.find((d) => d.dimension === "growth_trajectory");
      const leaderDim = score?.dimensions.find((d) => d.dimension === "leadership_potential");
      if (!groups[key]) groups[key] = { scores: [], growth: [], leadership: [] };
      groups[key].scores.push(score?.overall_score ?? 0);
      if (growthDim) groups[key].growth.push(growthDim.score);
      if (leaderDim) groups[key].leadership.push(leaderDim.score);
    }

    return groupsFor(scorer)
      .filter(({ key }) => groups[key])
      .map(({ key, label }) => {
        const data = groups[key];
        return {
          category: label,
          count: data.scores.length,
          avgScore: data.scores.reduce((a, b) => a + b, 0) / data.scores.length,
          minScore: Math.min(...data.scores),
          maxScore: Math.max(...data.scores),
          avgGrowth: data.growth.length > 0 ? data.growth.reduce((a, b) => a + b, 0) / data.growth.length : 0,
          avgLeadership:
            data.leadership.length > 0 ? data.leadership.reduce((a, b) => a + b, 0) / data.leadership.length : 0,
        };
      });
  }, [ranked, scorer]);

  return (
    <section>
      <h4 className="text-sm font-semibold text-[#141414] uppercase tracking-wider mb-1">Score distribution (legacy)</h4>
      <p style={{ fontSize: "14px", color: "#666", marginBottom: "20px" }}>
        Score distribution by {scorer === "baseline" ? "file completeness" : "recommendation category"}. Shows how
        candidates are distributed; it cannot show whether scoring treats groups of applicants differently.
      </p>
      {auditStats.length === 0 ? (
        <p className="text-sm text-[#969696] italic">No scored candidates to group.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full" style={{ fontSize: "14px" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #ddd", color: "#888" }}>
                <th style={{ textAlign: "left", padding: "10px 16px 10px 0", fontWeight: 500 }}>Category</th>
                <th style={{ textAlign: "right", padding: "10px 12px", fontWeight: 500 }}>Count</th>
                <th style={{ textAlign: "right", padding: "10px 12px", fontWeight: 500 }}>Avg Score</th>
                <th style={{ textAlign: "right", padding: "10px 12px", fontWeight: 500 }}>Range</th>
                <th style={{ textAlign: "right", padding: "10px 12px", fontWeight: 500 }}>Avg Growth</th>
                <th style={{ textAlign: "right", padding: "10px 12px", fontWeight: 500 }}>Avg Leadership</th>
                <th style={{ textAlign: "left", padding: "10px 0 10px 16px", fontWeight: 500, width: "160px" }}>Distribution</th>
              </tr>
            </thead>
            <tbody>
              {auditStats.map((s) => (
                <tr key={s.category} style={{ borderBottom: "1px solid #eee" }}>
                  <td style={{ padding: "10px 16px 10px 0", fontWeight: 600, color: "#141414" }}>{s.category}</td>
                  <td style={{ textAlign: "right", padding: "10px 12px", color: "#555" }}>{s.count}</td>
                  <td style={{ textAlign: "right", padding: "10px 12px" }}>
                    <span style={{ fontFamily: "monospace", fontWeight: 600, color: "#141414" }}>{s.avgScore.toFixed(1)}</span>
                  </td>
                  <td style={{ textAlign: "right", padding: "10px 12px", color: "#888", fontFamily: "monospace" }}>
                    {s.minScore.toFixed(0)}-{s.maxScore.toFixed(0)}
                  </td>
                  <td style={{ textAlign: "right", padding: "10px 12px", fontFamily: "monospace", color: "#c1f11d" }}>
                    {s.avgGrowth.toFixed(1)}
                  </td>
                  <td style={{ textAlign: "right", padding: "10px 12px", fontFamily: "monospace", color: "#c1f11d" }}>
                    {s.avgLeadership.toFixed(1)}
                  </td>
                  <td style={{ padding: "10px 0 10px 16px" }}>
                    <div style={{ flex: 1, height: "16px", backgroundColor: "#eee", borderRadius: "8px", overflow: "hidden" }}>
                      <div
                        style={{ height: "100%", backgroundColor: "#c1f11d", borderRadius: "8px", width: `${Math.min(s.avgScore, 100)}%` }}
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div style={{ marginTop: "20px", padding: "16px", backgroundColor: "#f0f7e0", borderRadius: "12px", border: "1px solid rgba(193,241,29,0.3)" }}>
        <p style={{ fontSize: "13px", color: "#555" }}>
          <strong style={{ color: "#141414" }}>Interpretation:</strong> The system evaluates candidates based on their
          individual merits — leadership potential, growth trajectory, motivation, and communication. Background factors
          like school type are not used as success predictors.
        </p>
      </div>
    </section>
  );
}
