"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { api } from "@/lib/api";
import type {
  RankedCandidate,
  CandidateScore,
  AIDetectionResult,
  Candidate,
  DimensionScore,
} from "@/lib/types";

const DIMENSION_KEYS = [
  "academic_strength",
  "leadership_potential",
  "motivation_values",
  "growth_trajectory",
  "communication",
] as const;

const DIMENSION_LABELS: Record<string, string> = {
  academic_strength: "Academic",
  leadership_potential: "Leadership",
  motivation_values: "Motivation",
  growth_trajectory: "Growth",
  communication: "Communication",
};

const DEFAULT_WEIGHTS: Record<string, number> = {
  academic_strength: 0.15,
  leadership_potential: 0.25,
  motivation_values: 0.25,
  growth_trajectory: 0.2,
  communication: 0.15,
};

const DIMENSION_WEIGHTS = DEFAULT_WEIGHTS;

function Badge({ label, color }: { label: string; color: string }) {
  const colors: Record<string, string> = {
    green: "bg-[#c1f11d] text-[#141414]",
    yellow: "bg-amber-400 text-[#141414]",
    red: "bg-red-500 text-white",
    blue: "bg-[#141414] text-white",
    gray: "bg-[#eae9e9] text-[#141414]",
  };
  return (
    <span
      className={`inline-block px-2.5 py-1 rounded-full text-sm font-medium ${colors[color] || colors.gray}`}
    >
      {label}
    </span>
  );
}

function RecommendationBadge({ rec }: { rec: string }) {
  if (rec === "recommend" || rec === "shortlist")
    return <Badge label="Recommend" color="green" />;
  if (rec === "consider" || rec === "review")
    return <Badge label="Consider" color="yellow" />;
  return <Badge label="Needs Attention" color="red" />;
}
// Note: these are AI-generated recommendations only — final decisions are made by the committee

function ScoreBar({ score, max = 100 }: { score: number; max?: number }) {
  const pct = Math.min((score / max) * 100, 100);
  const color =
    pct >= 70
      ? "bg-[#c1f11d]"
      : pct >= 50
        ? "bg-amber-400"
        : "bg-red-400";
  return (
    <div className="flex items-center gap-3 w-full">
      <div className="flex-1 h-3 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-sm font-mono w-9 text-right">{score.toFixed(0)}</span>
    </div>
  );
}

function ScoreBarDark({ score, max = 100 }: { score: number; max?: number }) {
  const pct = Math.min((score / max) * 100, 100);
  const color =
    pct >= 70
      ? "bg-[#c1f11d]"
      : pct >= 50
        ? "bg-amber-400"
        : "bg-red-400";
  return (
    <div className="flex items-center gap-3 w-full">
      <div className="flex-1 h-3 bg-[#333] rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-sm font-mono w-9 text-right text-gray-300">{score.toFixed(0)}</span>
    </div>
  );
}

function DimensionDetail({ dim }: { dim: DimensionScore }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-gray-200 last:border-0 py-3">
      <button
        className="w-full flex items-center justify-between text-left"
        onClick={() => setOpen(!open)}
      >
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-1">
            <span className="text-base font-medium text-gray-800">
              {DIMENSION_LABELS[dim.dimension] || dim.dimension}
            </span>
            <span className="text-xs text-gray-400">
              {(DIMENSION_WEIGHTS[dim.dimension] * 100).toFixed(0)}%
            </span>
            <Badge
              label={dim.confidence}
              color={
                dim.confidence === "high"
                  ? "green"
                  : dim.confidence === "medium"
                    ? "yellow"
                    : "red"
              }
            />
          </div>
          <ScoreBar score={dim.score} />
        </div>
        <span className="ml-3 text-gray-400 text-sm">{open ? "−" : "+"}</span>
      </button>
      {open && (
        <div className="mt-3 pl-3 text-sm space-y-3">
          <p className="text-gray-600">{dim.explanation}</p>
          {dim.evidence_quotes.length > 0 && (
            <div>
              <p className="font-medium text-gray-500 mb-1">Evidence:</p>
              {dim.evidence_quotes.map((q, i) => (
                <blockquote
                  key={i}
                  className="border-l-2 border-[#c1f11d] pl-3 text-gray-500 italic mb-1"
                >
                  &ldquo;{q}&rdquo;
                </blockquote>
              ))}
            </div>
          )}
          {dim.positive_factors.length > 0 && (
            <div>
              <p className="font-medium text-[#141414] mb-1">Strengths:</p>
              <ul className="list-disc list-inside text-gray-600">
                {dim.positive_factors.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </div>
          )}
          {dim.concerns.length > 0 && (
            <div>
              <p className="font-medium text-red-600 mb-1">Concerns:</p>
              <ul className="list-disc list-inside text-gray-600">
                {dim.concerns.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function CandidateCard({
  ranked,
  onSelect,
}: {
  ranked: RankedCandidate;
  onSelect: () => void;
}) {
  const score = ranked.baseline_score || ranked.ai_score;
  const c = ranked.candidate;
  return (
    <div
      className="bg-white rounded-2xl border border-gray-200 p-6 cursor-pointer transition-all duration-200 hover:border-[#c1f11d] hover:shadow-[0_0_20px_rgba(193,241,29,0.25)] hover:-translate-y-1"
      onClick={onSelect}
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-3">
            <span className="w-10 h-10 rounded-full bg-[#c1f11d] text-[#141414] flex items-center justify-center text-base font-bold">
              {ranked.rank}
            </span>
            <h3 className="font-semibold text-lg text-gray-900">{c.name}</h3>
          </div>
          <p className="text-sm text-gray-500 mt-1 ml-[52px]">
            {c.id} &middot; Age {c.age} &middot;{" "}
            {c.application.education.school_type} &middot; GPA{" "}
            {c.application.education.gpa}
          </p>
        </div>
        {score && <RecommendationBadge rec={score.recommendation} />}
      </div>
      {score && (
        <>
          <div className="flex items-center gap-3 mb-4">
            <span className="text-3xl font-bold text-[#141414]">
              {score.overall_score.toFixed(1)}
            </span>
            <span className="text-sm text-gray-400">/ 100</span>
            <Badge
              label={score.scorer_type.toUpperCase()}
              color={score.scorer_type === "ai" ? "blue" : "gray"}
            />
          </div>
          <div className="space-y-2">
            {score.dimensions.map((d) => (
              <div key={d.dimension} className="flex items-center gap-3">
                <span className="text-xs text-gray-500 w-24 truncate">
                  {DIMENSION_LABELS[d.dimension] || d.dimension}
                </span>
                <ScoreBar score={d.score} />
              </div>
            ))}
          </div>
        </>
      )}
      {/* Sparse Profile badge */}
      {(() => {
        const missingInterview = !c.interview_transcript || c.interview_transcript.trim() === "";
        const missingRec = !c.recommendation_summary || c.recommendation_summary.trim() === "";
        const missingExtras = c.application.extracurriculars.length === 0;
        const isSparse = missingInterview || missingRec || missingExtras;
        if (!isSparse) return null;
        return (
          <div className="mt-3 px-3 py-2 rounded-xl bg-amber-50 border border-amber-200">
            <span className="text-xs font-semibold text-amber-700">Sparse Profile</span>
            <p className="text-xs text-amber-600 mt-0.5">Weight shifted to Essay &amp; Teaching Challenge</p>
          </div>
        );
      })()}
      <div className="mt-4 flex flex-wrap gap-1.5">
        {c.application.languages.map((l) => (
          <Badge key={l} label={l} color="blue" />
        ))}
      </div>
    </div>
  );
}

type FeynmanScore = {
  clarity: number; patience: number; empathy: number; adaptability: number;
  quiz_transfer_score: number; overall_score: number; summary: string;
};

function CandidateDetail({
  candidate,
  score,
  aiDetection,
  feynmanScore,
  onClose,
  onDetectAI,
  onOverride,
  detectLoading,
}: {
  candidate: Candidate;
  score: CandidateScore | null;
  aiDetection: AIDetectionResult | null;
  feynmanScore: FeynmanScore | null;
  onClose: () => void;
  onDetectAI: () => void;
  onOverride: (dimension: string, value: number, note: string) => void;
  detectLoading: boolean;
}) {
  const [overrideDim, setOverrideDim] = useState("");
  const [overrideVal, setOverrideVal] = useState(50);
  const [overrideNote, setOverrideNote] = useState("");

  const c = candidate;
  const app = c.application;

  return (
    <div className="fixed inset-0 flex items-center justify-center p-6" style={{ zIndex: 200 }}>
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-white shadow-2xl overflow-y-auto rounded-2xl">
        <div className="sticky top-0 bg-white z-10 px-8 py-5 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-[#141414]">{c.name}</h2>
            <p className="text-base text-gray-500">
              {c.id} &middot; Age {c.age}
            </p>
          </div>
          <button
            className="w-10 h-10 rounded-full bg-[#eae9e9] hover:bg-[#141414] hover:text-white text-[#141414] flex items-center justify-center text-xl transition-colors"
            onClick={onClose}
          >
            &times;
          </button>
        </div>

        <div className="p-8 space-y-8">
          {/* Education */}
          <section>
            <h3 className="text-base font-semibold text-[#141414] uppercase tracking-wider mb-3 flex items-center gap-3">
              <span className="w-1.5 h-5 bg-[#c1f11d] rounded-full inline-block" />
              Education
            </h3>
            <div className="grid grid-cols-2 gap-3 text-base">
              <div>
                <span className="text-gray-500">School:</span>{" "}
                {app.education.school_type}
              </div>
              <div>
                <span className="text-gray-500">GPA:</span>{" "}
                {app.education.gpa}/4.0
              </div>
            </div>
            {app.education.academic_achievements.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {app.education.academic_achievements.map((a, i) => (
                  <Badge key={i} label={a} color="blue" />
                ))}
              </div>
            )}
          </section>

          {/* Extracurriculars */}
          {app.extracurriculars.length > 0 && (
            <section>
              <h3 className="text-base font-semibold text-[#141414] uppercase tracking-wider mb-3 flex items-center gap-3">
                <span className="w-1.5 h-5 bg-[#c1f11d] rounded-full inline-block" />
                Extracurriculars
              </h3>
              <div className="space-y-2 text-base">
                {app.extracurriculars.map((ec, i) => (
                  <div key={i} className="flex justify-between">
                    <span>
                      {ec.activity}{" "}
                      <span className="text-gray-400">({ec.role})</span>
                    </span>
                    <span className="text-gray-400">
                      {ec.duration_months} mo
                    </span>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Projects */}
          {app.projects.length > 0 && (
            <section>
              <h3 className="text-base font-semibold text-[#141414] uppercase tracking-wider mb-3 flex items-center gap-3">
                <span className="w-1.5 h-5 bg-[#c1f11d] rounded-full inline-block" />
                Projects
              </h3>
              {app.projects.map((p, i) => (
                <div key={i} className="mb-3 text-base">
                  <p className="font-medium">
                    {p.name}{" "}
                    <span className="text-gray-400">({p.role})</span>
                  </p>
                  {p.impact && (
                    <p className="text-gray-500 text-sm">{p.impact}</p>
                  )}
                </div>
              ))}
            </section>
          )}

          {/* Skills & Languages */}
          <section>
            <h3 className="text-base font-semibold text-[#141414] uppercase tracking-wider mb-3 flex items-center gap-3">
              <span className="w-1.5 h-5 bg-[#c1f11d] rounded-full inline-block" />
              Skills & Languages
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {app.skills.map((s) => (
                <Badge key={s} label={s} color="gray" />
              ))}
              {app.languages.map((l) => (
                <Badge key={l} label={l} color="blue" />
              ))}
            </div>
          </section>

          {/* Essay */}
          <section>
            <h3 className="text-base font-semibold text-[#141414] uppercase tracking-wider mb-3 flex items-center gap-3">
              <span className="w-1.5 h-5 bg-[#c1f11d] rounded-full inline-block" />
              Essay
            </h3>
            <p className="text-sm text-gray-400 mb-2">
              Prompt: &ldquo;{c.essay.prompt}&rdquo; &middot;{" "}
              {c.essay.word_count} words
            </p>
            <div className="bg-[#eae9e9] rounded-2xl p-5 text-base whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto">
              {c.essay.text}
            </div>
          </section>

          {/* Interview */}
          {c.interview_transcript && (
            <section>
              <h3 className="text-base font-semibold text-[#141414] uppercase tracking-wider mb-3 flex items-center gap-3">
                <span className="w-1.5 h-5 bg-[#c1f11d] rounded-full inline-block" />
                Interview Transcript
              </h3>
              <div className="bg-[#eae9e9] rounded-2xl p-5 text-base whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
                {c.interview_transcript}
              </div>
            </section>
          )}

          {/* Recommendation */}
          {c.recommendation_summary && (
            <section>
              <h3 className="text-base font-semibold text-[#141414] uppercase tracking-wider mb-3 flex items-center gap-3">
                <span className="w-1.5 h-5 bg-[#c1f11d] rounded-full inline-block" />
                Recommendation
              </h3>
              <div className="bg-[#eae9e9] rounded-2xl p-5 text-base">
                {c.recommendation_summary}
              </div>
            </section>
          )}

          {/* Scoring breakdown */}
          {score && (
            <section>
              <h3 className="text-base font-semibold text-[#141414] uppercase tracking-wider mb-3 flex items-center gap-3">
                <span className="w-1.5 h-5 bg-[#c1f11d] rounded-full inline-block" />
                Score Breakdown ({score.scorer_type.toUpperCase()})
              </h3>
              <div className="flex items-center gap-4 mb-4">
                <span className="text-4xl font-bold text-[#141414]">
                  {score.overall_score.toFixed(1)}
                </span>
                <RecommendationBadge rec={score.recommendation} />
              </div>
              {/* AI Insight */}
              {score.dimensions.length > 0 && (() => {
                const sorted = [...score.dimensions].sort((a, b) => b.score - a.score);
                const highest = sorted[0];
                const lowest = sorted[sorted.length - 1];
                const highLabel = DIMENSION_LABELS[highest.dimension] || highest.dimension;
                const lowLabel = DIMENSION_LABELS[lowest.dimension] || lowest.dimension;
                const missExplanation =
                  lowest.dimension === "growth_trajectory"
                    ? "growth potential not captured by transcripts alone"
                    : lowest.dimension === "communication"
                      ? "communication nuance often lost in paper reviews"
                      : `lower ${lowLabel} signal that may improve with holistic review`;
                return (
                  <div
                    className="rounded-2xl p-5 mb-4"
                    style={{ background: "linear-gradient(180deg, #252525, #0F0F0F)" }}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span className="w-1.5 h-5 bg-[#c1f11d] rounded-full inline-block" />
                      <span className="text-sm font-semibold text-[#c1f11d]">AI Insight</span>
                    </div>
                    <p className="text-sm text-gray-300 leading-relaxed">
                      Strong signal in <span className="text-white font-medium">{highLabel}</span> ({highest.score.toFixed(0)}).
                      {" "}Traditional screening would miss {missExplanation}.
                    </p>
                  </div>
                );
              })()}
              {score.summary && (
                <p className="text-base text-gray-600 mb-4">{score.summary}</p>
              )}
              <div className="space-y-2">
                {score.dimensions.map((d) => (
                  <DimensionDetail key={d.dimension} dim={d} />
                ))}
              </div>
            </section>
          )}

          {/* AI Detection */}
          <section>
            <h3 className="text-base font-semibold text-[#141414] uppercase tracking-wider mb-3 flex items-center gap-3">
              <span className="w-1.5 h-5 bg-[#c1f11d] rounded-full inline-block" />
              AI Content Detection
            </h3>
            {aiDetection ? (
              <div className="rounded-2xl p-5 text-base space-y-3" style={{ background: "linear-gradient(180deg, #252525, #0F0F0F)" }}>
                <div className="flex items-center gap-3">
                  <span className="font-medium text-white">Authenticity:</span>
                  <ScoreBarDark score={aiDetection.authenticity_score} />
                </div>
                <p className="text-gray-300">{aiDetection.explanation}</p>
                {aiDetection.flags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {aiDetection.flags.map((f, i) => (
                      <Badge key={i} label={f} color="red" />
                    ))}
                  </div>
                )}
                {aiDetection.stylometry && (
                  <div className="mt-3 border-t border-[#333] pt-3">
                    <p className="text-sm font-semibold text-gray-400 mb-2">
                      Stylometry Metrics (statistical, no AI)
                    </p>
                    <div className="grid grid-cols-2 gap-x-5 gap-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Vocabulary richness (TTR):</span>
                        <span className="font-mono text-gray-200">{aiDetection.stylometry.ttr.toFixed(3)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Sentence variance:</span>
                        <span className="font-mono text-gray-200">{aiDetection.stylometry.sentence_length_variance.toFixed(1)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Hapax ratio:</span>
                        <span className="font-mono text-gray-200">{aiDetection.stylometry.hapax_ratio.toFixed(3)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Formality ratio:</span>
                        <span className="font-mono text-gray-200">{aiDetection.stylometry.formality_ratio.toFixed(3)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Avg sentence length:</span>
                        <span className="font-mono text-gray-200">{aiDetection.stylometry.avg_sentence_length.toFixed(1)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Essay-interview overlap:</span>
                        <span className="font-mono text-gray-200">{aiDetection.stylometry.essay_interview_vocab_overlap.toFixed(3)}</span>
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      Reference: AI text typically has TTR 0.40-0.55, sentence variance 5-25, hapax 0.30-0.45
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <button
                className="px-5 py-2.5 bg-[#141414] text-[#c1f11d] rounded-xl text-base font-medium hover:scale-105 transition-transform disabled:opacity-50"
                onClick={onDetectAI}
                disabled={detectLoading}
              >
                {detectLoading ? "Analyzing..." : "Run AI Detection"}
              </button>
            )}
          </section>

          {/* Feynman Teaching Score */}
          {feynmanScore && (
            <section>
              <h3 className="text-base font-semibold text-[#141414] uppercase tracking-wider mb-3 flex items-center gap-3">
                <span className="w-1.5 h-5 bg-[#c1f11d] rounded-full inline-block" />
                Feynman Teaching Challenge
              </h3>
              <div className="rounded-2xl p-5 space-y-3 text-sm" style={{ background: "linear-gradient(180deg, #252525, #0F0F0F)" }}>
                <div className="flex items-center gap-3">
                  <span className="text-gray-300 w-28">Overall</span>
                  <ScoreBarDark score={feynmanScore.overall_score} />
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-gray-300 w-28">Clarity</span>
                  <ScoreBarDark score={feynmanScore.clarity} />
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-gray-300 w-28">Patience</span>
                  <ScoreBarDark score={feynmanScore.patience} />
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-gray-300 w-28">Empathy</span>
                  <ScoreBarDark score={feynmanScore.empathy} />
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-gray-300 w-28">Adaptability</span>
                  <ScoreBarDark score={feynmanScore.adaptability} />
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-gray-300 w-28">Quiz Transfer</span>
                  <ScoreBarDark score={feynmanScore.quiz_transfer_score} />
                </div>
                <p className="text-gray-400 mt-3">{feynmanScore.summary}</p>
              </div>
            </section>
          )}

          {/* Committee Override */}
          {score && (
            <section>
              <h3 className="text-base font-semibold text-[#141414] uppercase tracking-wider mb-3 flex items-center gap-3">
                <span className="w-1.5 h-5 bg-[#c1f11d] rounded-full inline-block" />
                Committee Override
              </h3>
              <div className="bg-[#eae9e9] rounded-2xl p-5 space-y-4">
                <select
                  className="w-full border border-gray-300 rounded-xl px-4 py-2.5 text-base bg-white focus:border-[#c1f11d] focus:ring-1 focus:ring-[#c1f11d] outline-none"
                  value={overrideDim}
                  onChange={(e) => setOverrideDim(e.target.value)}
                >
                  <option value="">Select dimension...</option>
                  {score.dimensions.map((d) => (
                    <option key={d.dimension} value={d.dimension}>
                      {DIMENSION_LABELS[d.dimension] || d.dimension} (current:{" "}
                      {d.score.toFixed(0)})
                    </option>
                  ))}
                </select>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={overrideVal}
                    onChange={(e) => setOverrideVal(Number(e.target.value))}
                    className="flex-1 accent-[#c1f11d]"
                  />
                  <span className="text-base font-mono w-9">{overrideVal}</span>
                </div>
                <input
                  type="text"
                  placeholder="Note (reason for override)"
                  className="w-full border border-gray-300 rounded-xl px-4 py-2.5 text-base bg-white focus:border-[#c1f11d] focus:ring-1 focus:ring-[#c1f11d] outline-none"
                  value={overrideNote}
                  onChange={(e) => setOverrideNote(e.target.value)}
                />
                <button
                  className="px-5 py-2.5 bg-[#c1f11d] text-[#141414] rounded-xl text-base font-semibold hover:scale-105 transition-transform disabled:opacity-50"
                  disabled={!overrideDim}
                  onClick={() => {
                    onOverride(overrideDim, overrideVal, overrideNote);
                    setOverrideDim("");
                    setOverrideNote("");
                  }}
                >
                  Apply Override
                </button>
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── Evaluation Settings ─────────────────────────────────────────────── */

function WeightSimulator({
  weights,
  onChange,
  onReset,
}: {
  weights: Record<string, number>;
  onChange: (key: string, value: number) => void;
  onReset: () => void;
}) {
  const [open, setOpen] = useState(false);
  const total = Object.values(weights).reduce((a, b) => a + b, 0);
  const isDefault = DIMENSION_KEYS.every(
    (k) => Math.abs(weights[k] - DEFAULT_WEIGHTS[k]) < 0.001
  );

  return (
    <div style={{ backgroundColor: "#fff", borderRadius: "30px", border: "2.68px solid #d7d7d7", padding: "15px", marginBottom: "16px" }}>
      <button
        className="w-full flex items-center text-left"
        style={{ backgroundColor: "#eae9e9", borderRadius: "15px", padding: "20px", border: "none", cursor: "pointer", gap: "15px" }}
        onClick={() => setOpen(!open)}
      >
        <div style={{ width: "53px", height: "53px", backgroundColor: "#141414", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <img src="/assets/Settings.svg" alt="" style={{ width: "28px", height: "28px" }} />
        </div>
        <div className="flex items-center gap-3">
          <span style={{ fontSize: "20px", fontWeight: 600, color: "#141414" }}>Evaluation Settings</span>
          {!isDefault && (
            <span className="text-xs bg-[#c1f11d] text-[#141414] px-2.5 py-1 rounded-full font-medium">
              Custom weights active
            </span>
          )}
        </div>
        <span className="text-gray-400 text-sm">{open ? "−" : "+"}</span>
      </button>
      {open && (
        <div style={{ padding: "20px 24px 24px", borderTop: "1px solid #ddd" }}>
          <p style={{ fontSize: "14px", color: "#666", marginBottom: "20px" }}>
            Configure your evaluation rubric. Adjust how much each dimension contributes to the overall score. Rankings update live.
          </p>
          <div className="space-y-4">
            {DIMENSION_KEYS.map((key) => (
              <div key={key} className="flex items-center gap-3">
                <span style={{ fontSize: "14px", color: "#555", width: "120px" }}>{DIMENSION_LABELS[key]}</span>
                <input
                  type="range"
                  min={0}
                  max={50}
                  value={Math.round(weights[key] * 100)}
                  onChange={(e) => onChange(key, parseInt(e.target.value) / 100)}
                  className="flex-1 h-2 accent-[#c1f11d]"
                />
                <span style={{ fontSize: "14px", fontFamily: "monospace", color: "#333", width: "48px", textAlign: "right" }}>
                  {Math.round(weights[key] * 100)}%
                </span>
              </div>
            ))}
          </div>
          <div className="flex items-center justify-between" style={{ marginTop: "20px", paddingTop: "16px", borderTop: "1px solid #ddd" }}>
            <span style={{ fontSize: "14px", color: Math.abs(total - 1) > 0.01 ? "#dc2626" : "#888" }}>
              Total: {Math.round(total * 100)}%{Math.abs(total - 1) > 0.01 && " (should be 100%)"}
            </span>
            {!isDefault && (
              <button
                onClick={onReset}
                style={{ fontSize: "14px", color: "#c1f11d", background: "none", border: "none", cursor: "pointer", fontWeight: 600 }}
              >
                Reset to defaults
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Fairness Audit Panel ────────────────────────────────────────── */

function FairnessAudit({ ranked }: { ranked: RankedCandidate[] }) {
  const [open, setOpen] = useState(false);

  const auditStats = useMemo(() => {
    const groups: Record<string, { scores: number[]; growth: number[]; leadership: number[] }> = {};

    for (const r of ranked) {
      const rec = (r.baseline_score || r.ai_score)?.recommendation ?? "unknown";
      const category = (rec === "recommend" || rec === "shortlist") ? "Recommend" :
                       (rec === "consider" || rec === "review") ? "Consider" : "Needs Attention";
      const score = (r.baseline_score || r.ai_score)?.overall_score ?? 0;
      const growthDim = (r.baseline_score || r.ai_score)?.dimensions.find(d => d.dimension === "growth_trajectory");
      const leaderDim = (r.baseline_score || r.ai_score)?.dimensions.find(d => d.dimension === "leadership_potential");
      if (!groups[category]) groups[category] = { scores: [], growth: [], leadership: [] };
      groups[category].scores.push(score);
      if (growthDim) groups[category].growth.push(growthDim.score);
      if (leaderDim) groups[category].leadership.push(leaderDim.score);
    }

    return ["Recommend", "Consider", "Needs Attention"]
      .filter(cat => groups[cat])
      .map((category) => {
        const data = groups[category];
        return {
          category,
          count: data.scores.length,
          avgScore: data.scores.reduce((a, b) => a + b, 0) / data.scores.length,
          minScore: Math.min(...data.scores),
          maxScore: Math.max(...data.scores),
          avgGrowth: data.growth.length > 0 ? data.growth.reduce((a, b) => a + b, 0) / data.growth.length : 0,
          avgLeadership: data.leadership.length > 0 ? data.leadership.reduce((a, b) => a + b, 0) / data.leadership.length : 0,
        };
      });
  }, [ranked]);

  return (
    <div style={{ backgroundColor: "#fff", borderRadius: "30px", border: "2.68px solid #d7d7d7", padding: "15px", marginBottom: "16px" }}>
      <button
        className="w-full flex items-center text-left"
        style={{ backgroundColor: "#eae9e9", borderRadius: "15px", padding: "20px", border: "none", cursor: "pointer", gap: "15px" }}
        onClick={() => setOpen(!open)}
      >
        <div style={{ width: "53px", height: "53px", backgroundColor: "#141414", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <img src="/assets/Scales.svg" alt="" style={{ width: "28px", height: "28px" }} />
        </div>
        <span style={{ fontSize: "20px", fontWeight: 600, color: "#141414" }}>Fairness Audit</span>
      </button>
      {open && (
        <div style={{ padding: "20px 24px 24px", borderTop: "1px solid #ddd" }}>
          <p style={{ fontSize: "14px", color: "#666", marginBottom: "20px" }}>
            Score distribution by recommendation category. Shows how candidates are distributed and whether the AI scoring is balanced.
          </p>
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
                    <td style={{ padding: "10px 16px 10px 0", fontWeight: 600, color: "#141414" }}>
                      {s.category}
                    </td>
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
          <div style={{ marginTop: "20px", padding: "16px", backgroundColor: "#f0f7e0", borderRadius: "12px", border: "1px solid rgba(193,241,29,0.3)" }}>
            <p style={{ fontSize: "13px", color: "#555" }}>
              <strong style={{ color: "#141414" }}>Interpretation:</strong> The system evaluates candidates based on their individual merits — leadership potential, growth trajectory, motivation, and communication. Background factors like school type are not used as success predictors.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Dashboard() {
  const [rawRanked, setRawRanked] = useState<RankedCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [aiDetections, setAiDetections] = useState<
    Record<string, AIDetectionResult>
  >({});
  const [feynmanScores, setFeynmanScores] = useState<Record<string, FeynmanScore>>({});
  const [detectLoading, setDetectLoading] = useState(false);
  const [filter, setFilter] = useState<string>("all");
  const [weights, setWeights] = useState<Record<string, number>>({ ...DEFAULT_WEIGHTS });
  const [scrollProgress, setScrollProgress] = useState(0);

  const loadRanking = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.scoring.rank("baseline");
      setRawRanked(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRanking();
  }, [loadRanking]);

  // Scroll progress bar
  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = document.documentElement.scrollTop;
      const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      setScrollProgress(scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Client-side recomputation with custom weights — instant, no API call
  const ranked = useMemo(() => {
    const recomputed = rawRanked.map((r) => {
      const score = r.baseline_score || r.ai_score;
      if (!score) return r;

      const newOverall = score.dimensions.reduce(
        (sum, d) => sum + d.score * (weights[d.dimension] ?? 0.2),
        0
      );
      const roundedOverall = Math.round(newOverall * 10) / 10;
      const newRec =
        roundedOverall >= 70 ? "recommend" : roundedOverall >= 50 ? "consider" : "needs attention";

      const updatedScore = {
        ...score,
        overall_score: roundedOverall,
        recommendation: newRec,
      };

      return {
        ...r,
        baseline_score: r.baseline_score ? updatedScore : null,
        ai_score: r.ai_score ? updatedScore : null,
      };
    });

    // Re-sort by new overall score
    recomputed.sort((a, b) => {
      const sa = (a.baseline_score || a.ai_score)?.overall_score ?? 0;
      const sb = (b.baseline_score || b.ai_score)?.overall_score ?? 0;
      return sb - sa;
    });

    // Re-rank
    return recomputed.map((r, i) => ({ ...r, rank: i + 1 }));
  }, [rawRanked, weights]);

  const handleWeightChange = (key: string, value: number) => {
    setWeights((prev) => ({ ...prev, [key]: value }));
  };

  const handleWeightReset = () => {
    setWeights({ ...DEFAULT_WEIGHTS });
  };

  const selected = ranked.find((r) => r.candidate.id === selectedId);
  const selectedScore =
    selected?.baseline_score || selected?.ai_score || null;

  // Fetch Feynman score when candidate is selected
  useEffect(() => {
    if (!selectedId || feynmanScores[selectedId]) return;
    api.feynman.finish("").catch(() => {}); // no-op, we just fetch cached score
    fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/feynman/score/${selectedId}`)
      .then((r) => r.ok ? r.json() : null)
      .then((data) => {
        if (data) setFeynmanScores((prev) => ({ ...prev, [selectedId]: data }));
      })
      .catch(() => {});
  }, [selectedId, feynmanScores]);

  const handleDetectAI = async () => {
    if (!selectedId) return;
    setDetectLoading(true);
    try {
      const result = await api.analysis.detectAI(selectedId);
      setAiDetections((prev) => ({ ...prev, [selectedId]: result }));
    } catch {
      /* ignore */
    } finally {
      setDetectLoading(false);
    }
  };

  const handleOverride = async (
    dimension: string,
    value: number,
    note: string
  ) => {
    if (!selectedId) return;
    try {
      await api.scoring.override(selectedId, dimension, value, note);
      await loadRanking();
    } catch {
      /* ignore */
    }
  };

  const recGroup = (r: RankedCandidate): "recommend" | "consider" | "needs_attention" => {
    const rec = (r.baseline_score || r.ai_score)?.recommendation ?? "";
    if (rec === "recommend" || rec === "shortlist") return "recommend";
    if (rec === "consider" || rec === "review") return "consider";
    // handles "needs attention", "decline", or any other value
    return "needs_attention";
  };

  const isHiddenGem = (r: RankedCandidate): boolean => {
    const score = r.baseline_score || r.ai_score;
    if (!score) return false;
    const overall = score.overall_score;
    if (overall >= 65) return false;
    return score.dimensions.some((d) => d.score > 70);
  };

  const filtered =
    filter === "all"
      ? ranked
      : filter === "hidden_gem"
        ? ranked.filter((r) => isHiddenGem(r))
        : ranked.filter((r) => recGroup(r) === filter);

  const stats = {
    total: ranked.length,
    recommend: ranked.filter((r) => recGroup(r) === "recommend").length,
    consider: ranked.filter((r) => recGroup(r) === "consider").length,
    needsAttention: ranked.filter((r) => recGroup(r) === "needs_attention").length,
    hiddenGems: ranked.filter((r) => isHiddenGem(r)).length,
  };

  return (
    <main className="min-h-screen bg-[#eae9e9]">
      {/* Scroll progress bar */}
      <div
        className="fixed top-0 left-0 h-[3px] bg-[#c1f11d] z-[200] transition-all duration-150"
        style={{ width: `${scrollProgress}%` }}
      />

      {/* Nav */}
      <nav
        style={{
          position: "sticky",
          top: 0,
          zIndex: 100,
          backgroundColor: "#c1f11d",
          padding: "18px 60px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <img
          src="/assets/InVision U Dark.png"
          alt="inVision U"
          style={{ width: "169.33px", height: "27.86px" }}
        />
        <div style={{ display: "flex", alignItems: "center", gap: 0 }}>
          {[
            { href: "/", label: "Home" },
            { href: "/#apply", label: "Applicant Portal" },
            { href: "/teach", label: "Teaching Challenge" },
            { href: "/dashboard", label: "Admissions Dashboard", current: true },
          ].map((link, i) => (
            <div key={link.label} style={{ display: "flex", alignItems: "center" }}>
              {i > 0 && (
                <div style={{ width: "1px", height: "40px", backgroundColor: "#141414" }} />
              )}
              <a
                href={link.href}
                style={{
                  padding: "14px 22px",
                  borderRadius: "10px",
                  textDecoration: "none",
                  fontWeight: link.current ? 700 : 500,
                  color: "#141414",
                  fontSize: "18px",
                  whiteSpace: "nowrap",
                  transition: "background-color 0.2s",
                  backgroundColor: link.current ? "#deff70" : "transparent",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLElement).style.backgroundColor = "#deff70";
                }}
                onMouseLeave={(e) => {
                  if (!link.current) {
                    (e.currentTarget as HTMLElement).style.backgroundColor = "transparent";
                  }
                }}
              >
                {link.label}
              </a>
            </div>
          ))}
        </div>
      </nav>

      {/* Dark header with dots */}
      <div style={{ maxWidth: "1400px", margin: "0 auto", padding: "12px 40px 0", position: "relative" }}>
        <div style={{ backgroundColor: "#141414", borderRadius: "24px", overflow: "hidden", position: "relative", padding: "36px 40px 60px" }}>
          <img src="/assets/Dots.png" alt="" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", opacity: 0.3, pointerEvents: "none" }} />
          <div style={{ position: "relative", zIndex: 1, display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
            <div>
              <h1 style={{ fontSize: "36px", fontWeight: 700, color: "#c1f11d", marginBottom: "4px" }}>Admissions Dashboard</h1>
              <p style={{ fontSize: "16px", color: "#fff" }}>AI-Assisted Screening &middot; Human-in-the-Loop</p>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "15px", color: "#fff" }}>
              <span style={{ width: "9px", height: "9px", borderRadius: "50%", backgroundColor: "#c1f11d", display: "inline-block" }} />
              System active
            </div>
          </div>
        </div>

        {/* Stats bar — overlapping header */}
        <div style={{ position: "relative", zIndex: 2, marginTop: "-36px", display: "flex", gap: "8px", padding: "12px 16px", backgroundColor: "#fff", borderRadius: "20px", border: "2px solid #d7d7d7" }}>
          {[
            { key: "all", label: "Total candidates", count: stats.total },
            { key: "recommend", label: "Recommended", count: stats.recommend },
            { key: "consider", label: "Consider", count: stats.consider },
            { key: "needs_attention", label: "Needs Attention", count: stats.needsAttention },
            { key: "hidden_gem", label: "Hidden Gems", count: stats.hiddenGems },
          ].map((stat) => (
            <button
              key={stat.key}
              onClick={() => setFilter(stat.key)}
              style={{
                flex: 1,
                padding: "16px 16px",
                borderRadius: "12px",
                border: "none",
                backgroundColor: filter === stat.key ? "#c1f11d" : "#eae9e9",
                cursor: "pointer",
                textAlign: "left",
                transition: "all 0.2s ease",
              }}
            >
              <p style={{ fontSize: "32px", fontWeight: 700, color: "#141414", lineHeight: 1, marginBottom: "2px" }}>{stat.count}</p>
              <p style={{ fontSize: "13px", color: "#141414" }}>{stat.label}</p>
            </button>
          ))}
        </div>
      </div>

      <div style={{ maxWidth: "1400px", margin: "0 auto", padding: "16px 40px 0" }}>
        {/* Evaluation Settings + Fairness Audit */}
        <WeightSimulator
          weights={weights}
          onChange={handleWeightChange}
          onReset={handleWeightReset}
        />
        <FairnessAudit ranked={ranked} />

        {/* Error */}
        {error && (
          <div className="mb-5 p-4 bg-red-500/10 text-red-400 rounded-2xl text-base border border-red-500/20">
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="text-center py-14 text-gray-400 text-lg">
            Loading candidates...
          </div>
        )}

        {/* Candidate grid */}
        {!loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filtered.map((r) => (
              <CandidateCard
                key={r.candidate.id}
                ranked={r}
                onSelect={() => setSelectedId(r.candidate.id)}
              />
            ))}
          </div>
        )}

        {filtered.length === 0 && !loading && (
          <div className="text-center py-14 text-gray-400 text-lg">
            No candidates match this filter.
          </div>
        )}
      </div>

      {/* Detail panel */}
      {selected && (
        <CandidateDetail
          candidate={selected.candidate}
          score={selectedScore}
          aiDetection={aiDetections[selected.candidate.id] || null}
          feynmanScore={feynmanScores[selected.candidate.id] || null}
          onClose={() => setSelectedId(null)}
          onDetectAI={handleDetectAI}
          onOverride={handleOverride}
          detectLoading={detectLoading}
        />
      )}

      {/* Footer */}
      <footer style={{ backgroundColor: "#141414", position: "relative", overflow: "hidden", padding: "60px 0 40px", marginTop: "40px" }}>
        <img src="/assets/InVision U GRADIENT.svg" alt="" style={{ position: "absolute", bottom: "-30px", left: "50%", transform: "translateX(-50%)", width: "clamp(600px, 80vw, 1200px)", opacity: 0.08, pointerEvents: "none" }} />
        <div style={{ position: "relative", zIndex: 1, maxWidth: "1200px", margin: "0 auto", padding: "0 40px", textAlign: "center" }}>
          <img src="/assets/InVision U white.png" alt="inVision U" style={{ width: "169px", height: "auto", margin: "0 auto 16px" }} />
          <p style={{ fontSize: "14px", color: "#666", marginBottom: "24px" }}>AI-Assisted Evaluation System &mdash; All final admission decisions are made by the human admissions committee.</p>
          <div style={{ display: "flex", justifyContent: "center", gap: "32px", marginBottom: "32px" }}>
            {[{ href: "/", label: "Home" }, { href: "/#apply", label: "Apply" }, { href: "/teach", label: "Teaching Challenge" }, { href: "/dashboard", label: "Dashboard" }].map((link) => (
              <a key={link.label} href={link.href} style={{ fontSize: "14px", color: "#888", textDecoration: "none", transition: "color 0.2s" }}
                onMouseEnter={(e: React.MouseEvent<HTMLAnchorElement>) => (e.currentTarget.style.color = "#c1f11d")}
                onMouseLeave={(e: React.MouseEvent<HTMLAnchorElement>) => (e.currentTarget.style.color = "#888")}
              >{link.label}</a>
            ))}
          </div>
          <div style={{ borderTop: "1px solid #333", paddingTop: "20px", fontSize: "12px", color: "#555" }}>Powered by inDrive &middot; Built for Decentrathon 5.0</div>
        </div>
      </footer>
    </main>
  );
}
