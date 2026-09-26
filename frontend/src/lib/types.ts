export interface Education {
  school_type: string;
  gpa: number;
  academic_achievements: string[];
  years_of_study: number;
}

export interface Extracurricular {
  activity: string;
  duration_months: number;
  role: string;
}

export interface Project {
  name: string;
  role: string;
  impact: string;
}

export interface Essay {
  prompt: string;
  text: string;
  word_count: number;
}

export interface Application {
  education: Education;
  extracurriculars: Extracurricular[];
  projects: Project[];
  languages: string[];
  skills: string[];
}

export interface Candidate {
  id: string;
  name: string;
  age: number;
  application: Application;
  essay: Essay;
  interview_transcript: string;
  recommendation_summary: string;
  video_link: string;
  video_transcript: string;
}

export interface DimensionScore {
  dimension: string;
  score: number;
  confidence: "low" | "medium" | "high";
  explanation: string;
  evidence_quotes: string[];
  positive_factors: string[];
  concerns: string[];
}

export interface StylometryMetrics {
  ttr: number;
  avg_sentence_length: number;
  sentence_length_variance: number;
  avg_word_length: number;
  formality_ratio: number;
  hapax_ratio: number;
  essay_interview_vocab_overlap: number;
}

export interface AIDetectionResult {
  authenticity_score: number;
  flags: string[];
  explanation: string;
  stylometry: StylometryMetrics | null;
}

export interface CandidateScore {
  candidate_id: string;
  dimensions: DimensionScore[];
  overall_score: number;
  ai_detection: AIDetectionResult | null;
  recommendation: string;
  summary: string;
  scorer_type: string;
}

export interface CounterfactualProbeVariant {
  id: string;
  marker: string;
  changed_markers: string[];
  score: CandidateScore;
  signed_delta: number;
  competency_deltas: Record<string, number>;
  level_flips: string[];
}

export interface CounterfactualProbeResult {
  candidate_id: string;
  status: "live" | "cached_demo" | "fallback_demo";
  baseline: CandidateScore;
  variants: CounterfactualProbeVariant[];
  signed_delta: number;
  noise_sd: number;
  tolerance: number;
  flips_for_human_review: string[];
  changed_markers: string[];
  prompt_id: string;
  model_id: string;
  notice: string;
}

export interface CohortProbeCell {
  marker: string;
  competency: string;
  sampled_candidates: number;
  robust_count: number;
  robustness_rate: number;
  passed: boolean;
}

export interface CohortProbeReport {
  status: "live" | "cached" | "fallback";
  mode: "live" | "cached" | "fallback";
  sampled_candidates: number;
  markers: string[];
  competencies: string[];
  cells: CohortProbeCell[];
  failed_cells: CohortProbeCell[];
  passed: boolean;
  threshold: number;
  noise_sd: number;
  tolerance: number;
  fixture_hash: string;
  prompt_id: string;
  model_id: string;
  production_invariance: { score_path_changed: boolean; ranking_changed: boolean; recommendation_changed: boolean };
  live: Record<string, unknown> | null;
  cached: Record<string, unknown> | null;
  fallback: Record<string, unknown> | null;
}

export interface RankedCandidate {
  rank: number;
  candidate: Candidate;
  ai_score: CandidateScore | null;
  baseline_score: CandidateScore | null;
}

export type FeynmanScore = {
  clarity: number;
  patience: number;
  empathy: number;
  adaptability: number;
  quiz_transfer_score: number;
  overall_score: number;
  summary: string;
};

export type VideoAnalysis = {
  transcript: string;
  language_detected: string;
  authenticity_match: number;
  motivation_score: number;
  key_themes: string[];
  growth_signals: string[];
  concerns: string[];
  summary: string;
  is_mock: boolean;
};

// ── Evidence ledger (mirrors backend/ledger/schema.py, LED-03) ──────
// Change these only together with schema.py; the fixture copy in
// lib/fixtures/ is checked against the backend one by `npm run lint`.

export const LEDGER_SCHEMA_VERSION = "led-03.1";

export const COMPETENCIES = [
  "motivation_university",
  "motivation_major",
  "leadership_abilities",
  "teamwork",
  "values",
  "prior_experience",
  "intellect",
  "purpose_driven_leadership",
  "wounded_leadership",
] as const;
export type Competency = (typeof COMPETENCIES)[number];

/** The client's three BARS levels, plus the honest fourth state. `no_evidence`
 * is not `weak`, and never a zero: it means no behaviour was seen at all. */
export const LEVELS = ["weak", "normal", "high", "no_evidence"] as const;
export type Level = (typeof LEVELS)[number];

export const ATOLA_COMPONENTS = ["action", "thinking", "outcome", "learnings", "application", "none"] as const;
export type AtolaComponent = (typeof ATOLA_COMPONENTS)[number];

export const SOURCES = [
  "essay",
  "written_presentation",
  "video_transcript",
  "scenario",
  "interview_notes",
  "recommendation_letter",
  "ipsative_test",
] as const;
export type Source = (typeof SOURCES)[number];

export const EVIDENCE_STATUSES = ["present", "claimed_only", "contradicted", "not_assessable"] as const;
export type EvidenceStatus = (typeof EVIDENCE_STATUSES)[number];

export interface EvidenceItem {
  /** Verbatim, in the language the applicant used. */
  quote: string;
  source: Source;
  source_ref: string;
  /** -1 when the span could not be located in the raw source. */
  char_start: number;
  char_end: number;
  atola: AtolaComponent;
  status: EvidenceStatus;
  /** Computed by the backend: the quote is literally present in the source. */
  verified: boolean;
  indicator_hint: string;
}

export interface IndicatorRating {
  indicator_id: string;
  observed_level: Level;
  evidence: EvidenceItem[];
  note: string;
  /** Non-empty when the level that counts is lower than the observed one. Derived. */
  capped_reason: string;
}

export interface AttentionFlag {
  code: string;
  quote: string;
  source: Source | null;
  explanation: string;
}

export interface CompetencyRating {
  competency: Competency;
  indicators: IndicatorRating[];
  /** null when the rubric reserves this competency for humans. */
  level: Level | null;
  rule_applied: string;
  reserved_for_humans: boolean;
  /** What would move this to the next level, in anchor wording. */
  contrastive: string;
  probe_question: string;
  flags: AttentionFlag[];
  /** Derived from the evidence; the gaps are what interview probes are for. */
  atola_present: AtolaComponent[];
}

export interface CandidateLedger {
  /** Pseudonymous id; never a name. */
  applicant_ref: string;
  schema_version: string;
  rubric_version: string;
  model_judge: string;
  model_extract: string;
  prompt_version: string;
  competencies: CompetencyRating[];
}

// ── Committee overrides (backend/routers/overrides.py, COM-01) ──────

export interface ReasonCodeOption {
  code: string;
  label: string;
  note_required: boolean;
}

/** One committee change to a competency level. Append-only: a later override
 * is a new entry, and the AI level it was made against is kept alongside. */
export interface OverrideEntry {
  id: string;
  competency: Competency;
  /** What the committee saw when overriding: the previous override, else the
   * AI level. null for a competency with no AI level. */
  from_level: Level | null;
  to_level: Level;
  /** null only for a row written without a code (none via the API). */
  reason_code: string | null;
  note: string;
  ai_level: Level | null;
  /** "ledger": stored AI row; "client": what the card showed (fixture until LED-11). */
  ai_level_source: "ledger" | "client" | "none";
  author: { id: string; full_name: string; role: string };
  created_at: string;
}

export interface OverrideInput {
  competency: Competency;
  to_level: Level;
  reason_code: string;
  note: string;
  ai_level: Level | null;
}

// ── Attribute-grouped fairness audit (FAIR-07) ─────────────────────
// Mirrors backend/routers/fairness.py. Levels are counted per group, never
// averaged; the outcome is the share rated High.

export type AuditState = "ok" | "review_needed" | "not_enough_data";

export interface AuditGroup {
  group: string;
  n: number;
  share_of_pool: number;
  levels: Record<Level, number>;
  high_rate: number;
  no_evidence_rate: number;
  /** high_rate / the reference group's high_rate. Shown even when not judged. */
  impact_ratio: number | null;
  ci_low: number | null;
  ci_high: number | null;
  is_reference: boolean;
  state: AuditState;
  review_reason: "below_threshold" | "interval_crosses_threshold" | null;
}

export interface AuditCell {
  competency: Competency;
  pool: number;
  reference_group: string | null;
  groups: AuditGroup[];
}

export interface AuditDimension {
  dimension: string;
  undeclared: number;
  competencies: AuditCell[];
}

export interface FairnessAuditReport {
  source: "synthetic" | "db";
  applicants: number;
  applicants_with_levels: number;
  input_hash: string;
  method: {
    outcome: string;
    reference: string;
    interval: string;
    bootstrap_seed: number;
    n_bootstrap: number;
    review_threshold: number;
    min_group_n: number;
    min_group_share: number;
  };
  competencies: Competency[];
  dimensions: AuditDimension[];
  synthetic: {
    cohort_seed: number;
    size: number;
    planted_effects: { competency: string; group: string; effect: string }[];
    notice: string;
  } | null;
}

export interface EvaluationReport {
  status: "cached_demo" | "fallback_demo" | "live";
  fixture_version: string;
  fixture_hash: string;
  seed: number;
  prompt_id: string;
  rubric_id: string;
  model_id: string;
  cases: number;
  exact_level_rate: number;
  level_flip_rate: number;
  level_flip_count: number;
  probe_count: number;
  repeat_consistency: number;
  repeat_count_per_case: number;
  cross_lingual_agreement: number;
  cross_lingual_by_language: Record<string, number>;
  injection_suite: {
    cases: number;
    verified_injected_evidence: number;
    level_changes_vs_clean: number;
    passed: boolean;
  };
  noise_sd: number;
  tolerance: number;
  methodology_limits: string[];
  production_invariance: {
    score_path_changed: boolean;
    ranking_changed: boolean;
    recommendation_changed: boolean;
  };
  case_count_by: { competencies: number; levels: number; languages: number; variants: number };
}

export interface ModelCard {
  title: string;
  status: string;
  intended_use: string;
  out_of_scope_use: string[];
  provenance: {
    registration_id: string;
    report_mode: string;
    model_hash: string;
    prompt_hash: string;
    rubric_hash: string;
    evaluation_data_hash: string;
    split: { train_applicants: number; holdout_applicants: number; train_rows: number; holdout_rows: number; holdout_sealed: boolean; tuning_source: string };
    execution: { requested_mode: string; effective_mode: string; fallback_used: boolean; fallback_reason: string | null; live_result: unknown; cached_result: unknown };
  };
  metrics: {
    agreement: Array<{
      competency: string;
      n: number;
      qwk: number;
      icc: number | null;
      human_human_ceiling: { qwk: number | null; icc: number | null };
      calibration: Record<string, Record<string, number>>;
    }>;
    impact_ratios: Array<{ dimension: string; reference_group: string | null; groups: Array<{ group: string; n: number; impact_ratio: number | null; ci_low: number | null; ci_high: number | null; state: string }> }>;
    screening_safety: { lowest_band: string; admitted_in_lowest_band: number; safe: boolean; status: string };
  };
  abstention: { policy: string; failed_model_runs: number; no_evidence_state: string; production_effect: string };
  screening_safety: { lowest_band: string; admitted_in_lowest_band: number; safe: boolean; status: string };
  limitations: string[];
  impact_assessment: { legal_basis: string; scope: string; affected_people: string; risks: string[]; mitigations: string[]; human_oversight: string; monitoring: string; residual_risk: string };
  production_invariance: { score_path_changed: boolean; ranking_changed: boolean; recommendation_changed: boolean };
}

export interface HeldoutReport {
  manifest: { registration_id: string; report_mode: string; prompt_id: string; model_id: string; rubric_id: string; evaluation_data_hash: string; seed: { split: number; bootstrap: number; n_bootstrap: number } };
  provenance: { requested_mode: string; effective_mode: string; fallback_used: boolean; fallback_reason: string | null; live_result: unknown; cached_result: unknown };
  split: { train_applicants: number; holdout_applicants: number; train_rows: number; holdout_rows: number; holdout_sealed: boolean; tuning_source: string };
  holdout: { agreement: Array<{ competency: string; n: number; qwk: number | null; icc: number | null }>; impact_ratios: unknown[]; screening_safety: { lowest_band: string; admitted_in_lowest_band: number; safe: boolean; status: string } };
  production_invariance: { score_path_changed: boolean; ranking_changed: boolean; recommendation_changed: boolean };
}

export interface FunderMemo {
  title: string;
  audience: string;
  report_mode: string;
  holdout: { screening_safety: { lowest_band: string; admitted_in_lowest_band: number; safe: boolean; status: string } };
  impact_ratios: Array<{ dimension: string; reference_group: string | null; groups: Array<{ group: string; n: number; high_rate: number; impact_ratio: number | null; ci_low: number | null; ci_high: number | null; state: string }> }>;
  calibration: Array<{ competency: string; n: number; qwk: number | null; icc: number | null; calibration: Record<string, Record<string, number>> }>;
  abstention: { ratings: number; abstentions: number; abstention_rate: number; by_competency: Array<{ competency: string; ratings: number; abstentions: number; abstention_rate: number }>; definition: string };
  provenance: { registration_id: string; report_hash: string; evaluation_data_hash: string; prompt_hash: string; model_hash: string; rubric_hash: string; split_seed: number; bootstrap_seed: number; holdout_sealed: boolean; tuning_source: string };
  production_invariance: { score_path_changed: boolean; ranking_changed: boolean; recommendation_changed: boolean };
}

export interface HeldoutReproducibility {
  status: "reproduced" | "mismatch";
  ratings_recomputed: number;
  frozen_hashes: { prompt: string; rubric: string; data: string };
  provenance: { requested_mode: string; effective_mode: string; fallback_used: boolean; fallback_reason: string | null; live_result: unknown; cached_result: unknown; fallback_result: unknown };
  source_provenance: { requested_mode: string; effective_mode: string; fallback_used: boolean; fallback_reason: string | null; live_result: unknown; cached_result: unknown };
  production_invariance: { score_path_changed: boolean; ranking_changed: boolean; recommendation_changed: boolean };
  byte_identical: boolean;
  expected_hash: string;
  actual_hash: string;
  mismatches: { path: string; expected: unknown; actual: unknown }[];
}
