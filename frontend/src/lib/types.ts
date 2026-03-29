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

export interface RankedCandidate {
  rank: number;
  candidate: Candidate;
  ai_score: CandidateScore | null;
  baseline_score: CandidateScore | null;
}

export interface ComparisonResult {
  candidate_id: string;
  baseline_overall: number;
  ai_overall: number;
  overall_difference: number;
  dimensions: {
    dimension: string;
    baseline_score: number;
    ai_score: number | null;
    difference: number | null;
    baseline_explanation: string;
    ai_explanation: string;
  }[];
  baseline_recommendation: string;
  ai_recommendation: string;
}
