// Reading and summarising an evidence ledger on the client.
//
// Everything here is a view over data the backend produced. Levels, caps and
// ATOLA coverage are derived server-side (backend/ledger/schema.py, atola.py)
// and only displayed here, never recomputed, so the card cannot disagree with
// the rule that fired.

import {
  ATOLA_COMPONENTS,
  COMPETENCIES,
  EVIDENCE_STATUSES,
  LEVELS,
  SOURCES,
  type AtolaComponent,
  type CandidateLedger,
  type Competency,
  type CompetencyRating,
  type EvidenceItem,
  type Level,
} from "./types";

// ── Parsing ────────────────────────────────────────────────────────

class LedgerShapeError extends Error {
  constructor(path: string, message: string) {
    super(`Ledger does not match schema at ${path}: ${message}`);
  }
}

type Obj = Record<string, unknown>;

function obj(v: unknown, path: string): Obj {
  if (typeof v !== "object" || v === null || Array.isArray(v)) {
    throw new LedgerShapeError(path, "expected an object");
  }
  return v as Obj;
}

function arr(v: unknown, path: string): unknown[] {
  if (!Array.isArray(v)) throw new LedgerShapeError(path, "expected an array");
  return v;
}

function str(v: unknown, path: string): string {
  if (typeof v !== "string") throw new LedgerShapeError(path, "expected a string");
  return v;
}

function num(v: unknown, path: string): number {
  if (typeof v !== "number") throw new LedgerShapeError(path, "expected a number");
  return v;
}

function bool(v: unknown, path: string): boolean {
  if (typeof v !== "boolean") throw new LedgerShapeError(path, "expected a boolean");
  return v;
}

function oneOf<T extends string>(allowed: readonly T[], v: unknown, path: string): T {
  if (typeof v !== "string" || !(allowed as readonly string[]).includes(v)) {
    throw new LedgerShapeError(path, `expected one of ${allowed.join(", ")}, got ${JSON.stringify(v)}`);
  }
  return v as T;
}

function parseEvidence(v: unknown, path: string): EvidenceItem {
  const o = obj(v, path);
  return {
    quote: str(o.quote, `${path}.quote`),
    source: oneOf(SOURCES, o.source, `${path}.source`),
    source_ref: str(o.source_ref, `${path}.source_ref`),
    char_start: num(o.char_start, `${path}.char_start`),
    char_end: num(o.char_end, `${path}.char_end`),
    atola: oneOf(ATOLA_COMPONENTS, o.atola, `${path}.atola`),
    status: oneOf(EVIDENCE_STATUSES, o.status, `${path}.status`),
    verified: bool(o.verified, `${path}.verified`),
    indicator_hint: str(o.indicator_hint, `${path}.indicator_hint`),
  };
}

function parseCompetency(v: unknown, path: string): CompetencyRating {
  const o = obj(v, path);
  return {
    competency: oneOf(COMPETENCIES, o.competency, `${path}.competency`),
    indicators: arr(o.indicators, `${path}.indicators`).map((iv, i) => {
      const ip = `${path}.indicators[${i}]`;
      const io = obj(iv, ip);
      return {
        indicator_id: str(io.indicator_id, `${ip}.indicator_id`),
        observed_level: oneOf(LEVELS, io.observed_level, `${ip}.observed_level`),
        evidence: arr(io.evidence, `${ip}.evidence`).map((ev, j) => parseEvidence(ev, `${ip}.evidence[${j}]`)),
        note: str(io.note, `${ip}.note`),
        capped_reason: str(io.capped_reason, `${ip}.capped_reason`),
      };
    }),
    level: o.level === null ? null : oneOf(LEVELS, o.level, `${path}.level`),
    rule_applied: str(o.rule_applied, `${path}.rule_applied`),
    reserved_for_humans: bool(o.reserved_for_humans, `${path}.reserved_for_humans`),
    contrastive: str(o.contrastive, `${path}.contrastive`),
    probe_question: str(o.probe_question, `${path}.probe_question`),
    flags: arr(o.flags, `${path}.flags`).map((fv, i) => {
      const fp = `${path}.flags[${i}]`;
      const fo = obj(fv, fp);
      return {
        code: str(fo.code, `${fp}.code`),
        quote: str(fo.quote, `${fp}.quote`),
        source: fo.source === null ? null : oneOf(SOURCES, fo.source, `${fp}.source`),
        explanation: str(fo.explanation, `${fp}.explanation`),
      };
    }),
    atola_present: arr(o.atola_present, `${path}.atola_present`).map((a, i) =>
      oneOf(ATOLA_COMPONENTS, a, `${path}.atola_present[${i}]`),
    ),
  };
}

/** Validate untrusted JSON (the fixture now, the ledger API after LED-11). */
export function parseLedger(raw: unknown): CandidateLedger {
  const o = obj(raw, "$");
  return {
    applicant_ref: str(o.applicant_ref, "$.applicant_ref"),
    schema_version: str(o.schema_version, "$.schema_version"),
    rubric_version: str(o.rubric_version, "$.rubric_version"),
    model_judge: str(o.model_judge, "$.model_judge"),
    model_extract: str(o.model_extract, "$.model_extract"),
    prompt_version: str(o.prompt_version, "$.prompt_version"),
    competencies: arr(o.competencies, "$.competencies").map((c, i) => parseCompetency(c, `$.competencies[${i}]`)),
  };
}

// ── States ─────────────────────────────────────────────────────────

/** What one competency row shows. Six states, none of them a number.
 * `not_in_ledger` means the pipeline did not cover it (provisional rubric),
 * which is different again from having looked and found nothing. */
export type CompetencyState = Level | "reserved" | "not_in_ledger";

export function competencyState(rating: CompetencyRating | undefined): CompetencyState {
  if (!rating) return "not_in_ledger";
  if (rating.reserved_for_humans || rating.level === null) return "reserved";
  return rating.level;
}

/** Nine rows in the fixed rubric order, whether or not the ledger covers them. */
export function nineRows(ledger: CandidateLedger): { competency: Competency; rating?: CompetencyRating }[] {
  const byCompetency = new Map(ledger.competencies.map((r) => [r.competency, r]));
  return COMPETENCIES.map((competency) => ({ competency, rating: byCompetency.get(competency) }));
}

/** ATOLA components an interview could probe for (`none` is not a component). */
export const ATOLA_SEQUENCE: AtolaComponent[] = ["action", "thinking", "outcome", "learnings", "application"];

export function atolaGaps(rating: CompetencyRating): AtolaComponent[] {
  return ATOLA_SEQUENCE.filter((c) => !rating.atola_present.includes(c));
}

/** Verified quotes showing the behaviour, not merely asserting it. */
export function demonstratedEvidence(rating: CompetencyRating): { indicator_id: string; item: EvidenceItem }[] {
  return rating.indicators.flatMap((ind) =>
    ind.evidence
      .filter((item) => item.verified && item.status === "present")
      .map((item) => ({ indicator_id: ind.indicator_id, item })),
  );
}

/** For the interviewer: is there anything to verify, and of what kind? No level. */
export type EvidenceState = "demonstrated" | "claimed_only" | "no_evidence" | "live_only" | "not_in_ledger";

export function evidenceState(rating: CompetencyRating | undefined): EvidenceState {
  if (!rating) return "not_in_ledger";
  if (rating.reserved_for_humans) return "live_only";
  const verified = rating.indicators.flatMap((i) => i.evidence).filter((e) => e.verified);
  if (verified.length === 0) return "no_evidence";
  return verified.some((e) => e.status === "present") ? "demonstrated" : "claimed_only";
}

export interface LedgerStats {
  ledgers: number;
  competencyStates: Record<CompetencyState, number>;
  indicators: number;
  indicatorsWithoutEvidence: number;
  cappedIndicators: number;
  evidenceItems: number;
  unverifiedItems: number;
  flags: number;
}

/** Cohort health figures for the audit view. Counts, never averages of levels. */
export function ledgerStats(ledgers: CandidateLedger[]): LedgerStats {
  const stats: LedgerStats = {
    ledgers: ledgers.length,
    competencyStates: { high: 0, normal: 0, weak: 0, no_evidence: 0, reserved: 0, not_in_ledger: 0 },
    indicators: 0,
    indicatorsWithoutEvidence: 0,
    cappedIndicators: 0,
    evidenceItems: 0,
    unverifiedItems: 0,
    flags: 0,
  };
  for (const ledger of ledgers) {
    for (const { rating } of nineRows(ledger)) {
      stats.competencyStates[competencyState(rating)] += 1;
      if (!rating) continue;
      stats.flags += rating.flags.length;
      for (const ind of rating.indicators) {
        stats.indicators += 1;
        if (!ind.evidence.some((e) => e.verified)) stats.indicatorsWithoutEvidence += 1;
        if (ind.capped_reason) stats.cappedIndicators += 1;
        stats.evidenceItems += ind.evidence.length;
        stats.unverifiedItems += ind.evidence.filter((e) => !e.verified).length;
      }
    }
  }
  return stats;
}
