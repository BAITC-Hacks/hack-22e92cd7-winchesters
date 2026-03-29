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
    green: "bg-emerald-100 text-emerald-800",
    yellow: "bg-amber-100 text-amber-800",
    red: "bg-red-100 text-red-800",
    blue: "bg-blue-100 text-blue-800",
    gray: "bg-gray-100 text-gray-700",
  };
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${colors[color] || colors.gray}`}
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
      ? "bg-emerald-500"
      : pct >= 50
        ? "bg-amber-400"
        : "bg-red-400";
  return (
    <div className="flex items-center gap-2 w-full">
      <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono w-8 text-right">{score.toFixed(0)}</span>
    </div>
  );
}

function DimensionDetail({ dim }: { dim: DimensionScore }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-gray-100 last:border-0 py-2">
      <button
        className="w-full flex items-center justify-between text-left"
        onClick={() => setOpen(!open)}
      >
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium">
              {DIMENSION_LABELS[dim.dimension] || dim.dimension}
            </span>
            <span className="text-[10px] text-gray-400">
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
        <span className="ml-2 text-gray-400 text-xs">{open ? "−" : "+"}</span>
      </button>
      {open && (
        <div className="mt-2 pl-2 text-xs space-y-2">
          <p className="text-gray-600">{dim.explanation}</p>
          {dim.evidence_quotes.length > 0 && (
            <div>
              <p className="font-medium text-gray-500 mb-1">Evidence:</p>
              {dim.evidence_quotes.map((q, i) => (
                <blockquote
                  key={i}
                  className="border-l-2 border-indigo-300 pl-2 text-gray-500 italic mb-1"
                >
                  &ldquo;{q}&rdquo;
                </blockquote>
              ))}
            </div>
          )}
          {dim.positive_factors.length > 0 && (
            <div>
              <p className="font-medium text-emerald-700 mb-1">Strengths:</p>
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
      className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
      onClick={onSelect}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-indigo-600">
              #{ranked.rank}
            </span>
            <h3 className="font-semibold text-gray-900">{c.name}</h3>
          </div>
          <p className="text-xs text-gray-500 mt-0.5">
            {c.id} &middot; Age {c.age} &middot;{" "}
            {c.application.education.school_type} &middot; GPA{" "}
            {c.application.education.gpa}
          </p>
        </div>
        {score && <RecommendationBadge rec={score.recommendation} />}
      </div>
      {score && (
        <>
          <div className="flex items-center gap-3 mb-3">
            <span className="text-2xl font-bold">
              {score.overall_score.toFixed(1)}
            </span>
            <span className="text-xs text-gray-400">/ 100</span>
            <Badge
              label={score.scorer_type.toUpperCase()}
              color={score.scorer_type === "ai" ? "blue" : "gray"}
            />
          </div>
          <div className="space-y-1">
            {score.dimensions.map((d) => (
              <div key={d.dimension} className="flex items-center gap-2">
                <span className="text-[11px] text-gray-500 w-20 truncate">
                  {DIMENSION_LABELS[d.dimension] || d.dimension}
                </span>
                <ScoreBar score={d.score} />
              </div>
            ))}
          </div>
        </>
      )}
      <div className="mt-3 flex flex-wrap gap-1">
        {c.application.languages.map((l) => (
          <Badge key={l} label={l} color="blue" />
        ))}
      </div>
    </div>
  );
}

function CandidateDetail({
  candidate,
  score,
  aiDetection,
  onClose,
  onDetectAI,
  onOverride,
  detectLoading,
}: {
  candidate: Candidate;
  score: CandidateScore | null;
  aiDetection: AIDetectionResult | null;
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
    <div className="fixed inset-0 z-50 flex">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div className="relative ml-auto w-full max-w-2xl bg-white shadow-xl overflow-y-auto">
        <div className="sticky top-0 bg-white z-10 px-6 py-4 border-b flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold">{c.name}</h2>
            <p className="text-sm text-gray-500">
              {c.id} &middot; Age {c.age}
            </p>
          </div>
          <button
            className="text-gray-400 hover:text-gray-600 text-2xl"
            onClick={onClose}
          >
            &times;
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Education */}
          <section>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-2">
              Education
            </h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
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
              <div className="mt-1 flex flex-wrap gap-1">
                {app.education.academic_achievements.map((a, i) => (
                  <Badge key={i} label={a} color="blue" />
                ))}
              </div>
            )}
          </section>

          {/* Extracurriculars */}
          {app.extracurriculars.length > 0 && (
            <section>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-2">
                Extracurriculars
              </h3>
              <div className="space-y-1 text-sm">
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
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-2">
                Projects
              </h3>
              {app.projects.map((p, i) => (
                <div key={i} className="mb-2 text-sm">
                  <p className="font-medium">
                    {p.name}{" "}
                    <span className="text-gray-400">({p.role})</span>
                  </p>
                  {p.impact && (
                    <p className="text-gray-500 text-xs">{p.impact}</p>
                  )}
                </div>
              ))}
            </section>
          )}

          {/* Skills & Languages */}
          <section>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-2">
              Skills & Languages
            </h3>
            <div className="flex flex-wrap gap-1">
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
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-2">
              Essay
            </h3>
            <p className="text-xs text-gray-400 mb-1">
              Prompt: &ldquo;{c.essay.prompt}&rdquo; &middot;{" "}
              {c.essay.word_count} words
            </p>
            <div className="bg-gray-50 rounded-lg p-3 text-sm whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto">
              {c.essay.text}
            </div>
          </section>

          {/* Interview */}
          {c.interview_transcript && (
            <section>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-2">
                Interview Transcript
              </h3>
              <div className="bg-gray-50 rounded-lg p-3 text-sm whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
                {c.interview_transcript}
              </div>
            </section>
          )}

          {/* Recommendation */}
          {c.recommendation_summary && (
            <section>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-2">
                Recommendation
              </h3>
              <div className="bg-gray-50 rounded-lg p-3 text-sm">
                {c.recommendation_summary}
              </div>
            </section>
          )}

          {/* Scoring breakdown */}
          {score && (
            <section>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-2">
                Score Breakdown ({score.scorer_type.toUpperCase()})
              </h3>
              <div className="flex items-center gap-3 mb-3">
                <span className="text-3xl font-bold">
                  {score.overall_score.toFixed(1)}
                </span>
                <RecommendationBadge rec={score.recommendation} />
              </div>
              {score.summary && (
                <p className="text-sm text-gray-600 mb-3">{score.summary}</p>
              )}
              <div className="space-y-1">
                {score.dimensions.map((d) => (
                  <DimensionDetail key={d.dimension} dim={d} />
                ))}
              </div>
            </section>
          )}

          {/* AI Detection */}
          <section>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-2">
              AI Content Detection
            </h3>
            {aiDetection ? (
              <div className="bg-gray-50 rounded-lg p-3 text-sm space-y-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium">Authenticity:</span>
                  <ScoreBar score={aiDetection.authenticity_score} />
                </div>
                <p className="text-gray-600">{aiDetection.explanation}</p>
                {aiDetection.flags.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {aiDetection.flags.map((f, i) => (
                      <Badge key={i} label={f} color="red" />
                    ))}
                  </div>
                )}
                {aiDetection.stylometry && (
                  <div className="mt-2 border-t border-gray-200 pt-2">
                    <p className="text-xs font-semibold text-gray-500 mb-1">
                      Stylometry Metrics (statistical, no AI)
                    </p>
                    <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Vocabulary richness (TTR):</span>
                        <span className="font-mono">{aiDetection.stylometry.ttr.toFixed(3)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Sentence variance:</span>
                        <span className="font-mono">{aiDetection.stylometry.sentence_length_variance.toFixed(1)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Hapax ratio:</span>
                        <span className="font-mono">{aiDetection.stylometry.hapax_ratio.toFixed(3)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Formality ratio:</span>
                        <span className="font-mono">{aiDetection.stylometry.formality_ratio.toFixed(3)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Avg sentence length:</span>
                        <span className="font-mono">{aiDetection.stylometry.avg_sentence_length.toFixed(1)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Essay-interview overlap:</span>
                        <span className="font-mono">{aiDetection.stylometry.essay_interview_vocab_overlap.toFixed(3)}</span>
                      </div>
                    </div>
                    <p className="text-[10px] text-gray-400 mt-1">
                      Reference: AI text typically has TTR 0.40-0.55, sentence variance 5-25, hapax 0.30-0.45
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <button
                className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50"
                onClick={onDetectAI}
                disabled={detectLoading}
              >
                {detectLoading ? "Analyzing..." : "Run AI Detection"}
              </button>
            )}
          </section>

          {/* Committee Override */}
          {score && (
            <section>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-2">
                Committee Override
              </h3>
              <div className="bg-gray-50 rounded-lg p-3 space-y-2">
                <select
                  className="w-full border rounded px-2 py-1 text-sm"
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
                <div className="flex items-center gap-2">
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={overrideVal}
                    onChange={(e) => setOverrideVal(Number(e.target.value))}
                    className="flex-1"
                  />
                  <span className="text-sm font-mono w-8">{overrideVal}</span>
                </div>
                <input
                  type="text"
                  placeholder="Note (reason for override)"
                  className="w-full border rounded px-2 py-1 text-sm"
                  value={overrideNote}
                  onChange={(e) => setOverrideNote(e.target.value)}
                />
                <button
                  className="px-3 py-1.5 bg-amber-500 text-white rounded-lg text-sm hover:bg-amber-600 disabled:opacity-50"
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

/* ── Weight Simulator ─────────────────────────────────────────────── */

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
    <div className="bg-white rounded-xl border border-gray-200 mb-4">
      <button
        className="w-full flex items-center justify-between px-5 py-3 text-left"
        onClick={() => setOpen(!open)}
      >
        <div className="flex items-center gap-3">
          <svg className="w-5 h-5 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
          </svg>
          <span className="text-sm font-semibold text-gray-800">Weight Simulator</span>
          {!isDefault && (
            <span className="text-[10px] bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-medium">
              Custom weights active
            </span>
          )}
        </div>
        <span className="text-gray-400 text-xs">{open ? "−" : "+"}</span>
      </button>
      {open && (
        <div className="px-5 pb-5 border-t border-gray-100 pt-4">
          <p className="text-xs text-gray-500 mb-4">
            Adjust how much each dimension contributes to the overall score. Rankings update live.
          </p>
          <div className="space-y-3">
            {DIMENSION_KEYS.map((key) => (
              <div key={key} className="flex items-center gap-3">
                <span className="text-xs text-gray-600 w-24">{DIMENSION_LABELS[key]}</span>
                <input
                  type="range"
                  min={0}
                  max={50}
                  value={Math.round(weights[key] * 100)}
                  onChange={(e) => onChange(key, parseInt(e.target.value) / 100)}
                  className="flex-1 h-2 accent-indigo-600"
                />
                <span className="text-xs font-mono text-gray-700 w-10 text-right">
                  {Math.round(weights[key] * 100)}%
                </span>
              </div>
            ))}
          </div>
          <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-100">
            <span className={`text-xs ${Math.abs(total - 1) > 0.01 ? "text-red-500 font-medium" : "text-gray-400"}`}>
              Total: {Math.round(total * 100)}%{Math.abs(total - 1) > 0.01 && " (should be 100%)"}
            </span>
            {!isDefault && (
              <button
                onClick={onReset}
                className="text-xs text-indigo-600 hover:text-indigo-700 font-medium"
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

  const schoolStats = useMemo(() => {
    const groups: Record<string, { scores: number[]; growth: number[] }> = {};

    for (const r of ranked) {
      const school = r.candidate.application.education.school_type;
      const score = (r.baseline_score || r.ai_score)?.overall_score ?? 0;
      const growthDim = (r.baseline_score || r.ai_score)?.dimensions.find(
        (d) => d.dimension === "growth_trajectory"
      );
      if (!groups[school]) groups[school] = { scores: [], growth: [] };
      groups[school].scores.push(score);
      if (growthDim) groups[school].growth.push(growthDim.score);
    }

    return Object.entries(groups)
      .map(([school, data]) => ({
        school,
        count: data.scores.length,
        avgScore: data.scores.reduce((a, b) => a + b, 0) / data.scores.length,
        minScore: Math.min(...data.scores),
        maxScore: Math.max(...data.scores),
        avgGrowth: data.growth.length > 0
          ? data.growth.reduce((a, b) => a + b, 0) / data.growth.length
          : 0,
      }))
      .sort((a, b) => b.avgScore - a.avgScore);
  }, [ranked]);

  const overallAvg =
    ranked.length > 0
      ? ranked.reduce(
          (sum, r) =>
            sum + ((r.baseline_score || r.ai_score)?.overall_score ?? 0),
          0
        ) / ranked.length
      : 0;

  return (
    <div className="bg-white rounded-xl border border-gray-200 mb-4">
      <button
        className="w-full flex items-center justify-between px-5 py-3 text-left"
        onClick={() => setOpen(!open)}
      >
        <div className="flex items-center gap-3">
          <svg className="w-5 h-5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
          </svg>
          <span className="text-sm font-semibold text-gray-800">Fairness Audit</span>
        </div>
        <span className="text-gray-400 text-xs">{open ? "−" : "+"}</span>
      </button>
      {open && (
        <div className="px-5 pb-5 border-t border-gray-100 pt-4">
          <p className="text-xs text-gray-500 mb-4">
            Score distribution by school type. Overall scores should not be dominated by school type alone
            — growth trajectory compensates for resource differences.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-200 text-gray-500">
                  <th className="text-left py-2 pr-4 font-medium">School Type</th>
                  <th className="text-right py-2 px-2 font-medium">Count</th>
                  <th className="text-right py-2 px-2 font-medium">Avg Score</th>
                  <th className="text-right py-2 px-2 font-medium">Range</th>
                  <th className="text-right py-2 px-2 font-medium">Avg Growth</th>
                  <th className="text-left py-2 pl-4 font-medium w-40">Distribution</th>
                </tr>
              </thead>
              <tbody>
                {schoolStats.map((s) => {
                  const deviation = s.avgScore - overallAvg;
                  return (
                    <tr key={s.school} className="border-b border-gray-50">
                      <td className="py-2 pr-4 capitalize font-medium text-gray-800">
                        {s.school}
                      </td>
                      <td className="text-right py-2 px-2 text-gray-600">{s.count}</td>
                      <td className="text-right py-2 px-2">
                        <span className="font-mono font-medium">{s.avgScore.toFixed(1)}</span>
                        <span className={`ml-1 ${deviation >= 0 ? "text-emerald-600" : "text-red-500"}`}>
                          ({deviation >= 0 ? "+" : ""}{deviation.toFixed(1)})
                        </span>
                      </td>
                      <td className="text-right py-2 px-2 text-gray-500 font-mono">
                        {s.minScore.toFixed(0)}-{s.maxScore.toFixed(0)}
                      </td>
                      <td className="text-right py-2 px-2 font-mono text-indigo-600">
                        {s.avgGrowth.toFixed(1)}
                      </td>
                      <td className="py-2 pl-4">
                        <div className="flex items-center gap-1">
                          <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-indigo-400 rounded-full"
                              style={{ width: `${Math.min(s.avgScore, 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="mt-4 p-3 bg-emerald-50 rounded-lg">
            <p className="text-xs text-emerald-800">
              <strong>Interpretation:</strong> Growth trajectory scores differ by school type (by design —
              students from under-resourced schools get credit for overcoming more).
              Overall scores should show overlap across school types, proving that school background
              alone does not determine outcome.
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
  const [detectLoading, setDetectLoading] = useState(false);
  const [filter, setFilter] = useState<string>("all");
  const [weights, setWeights] = useState<Record<string, number>>({ ...DEFAULT_WEIGHTS });

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

  const filtered =
    filter === "all"
      ? ranked
      : ranked.filter((r) => recGroup(r) === filter);

  const stats = {
    total: ranked.length,
    recommend: ranked.filter((r) => recGroup(r) === "recommend").length,
    consider: ranked.filter((r) => recGroup(r) === "consider").length,
    needsAttention: ranked.filter((r) => recGroup(r) === "needs_attention").length,
  };

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="bg-white border-b px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-indigo-700">
              InVision U
            </h1>
            <p className="text-sm text-gray-500">
              Candidate Evaluation Dashboard
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <span className="inline-block w-2 h-2 rounded-full bg-emerald-400" />
              AI-Assisted Screening &middot; Human-in-the-Loop
            </div>
            <a
              href="/"
              className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
            >
              &larr; Home
            </a>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <button
            onClick={() => setFilter("all")}
            className={`rounded-xl p-4 text-left transition-colors ${filter === "all" ? "bg-indigo-600 text-white" : "bg-white border"}`}
          >
            <p className="text-2xl font-bold">{stats.total}</p>
            <p className="text-xs opacity-70">Total Candidates</p>
          </button>
          <button
            onClick={() => setFilter("recommend")}
            className={`rounded-xl p-4 text-left transition-colors ${filter === "recommend" ? "bg-emerald-600 text-white" : "bg-white border"}`}
          >
            <p className="text-2xl font-bold">{stats.recommend}</p>
            <p className="text-xs opacity-70">Recommended</p>
          </button>
          <button
            onClick={() => setFilter("consider")}
            className={`rounded-xl p-4 text-left transition-colors ${filter === "consider" ? "bg-amber-500 text-white" : "bg-white border"}`}
          >
            <p className="text-2xl font-bold">{stats.consider}</p>
            <p className="text-xs opacity-70">Consider</p>
          </button>
          <button
            onClick={() => setFilter("needs_attention")}
            className={`rounded-xl p-4 text-left transition-colors ${filter === "needs_attention" ? "bg-red-500 text-white" : "bg-white border"}`}
          >
            <p className="text-2xl font-bold">{stats.needsAttention}</p>
            <p className="text-xs opacity-70">Needs Attention</p>
          </button>
        </div>

        {/* Weight Simulator + Fairness Audit */}
        <WeightSimulator
          weights={weights}
          onChange={handleWeightChange}
          onReset={handleWeightReset}
        />
        <FairnessAudit ranked={ranked} />

        {/* Error */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="text-center py-12 text-gray-400">
            Loading candidates...
          </div>
        )}

        {/* Candidate grid */}
        {!loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
          <div className="text-center py-12 text-gray-400">
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
          onClose={() => setSelectedId(null)}
          onDetectAI={handleDetectAI}
          onOverride={handleOverride}
          detectLoading={detectLoading}
        />
      )}
    </main>
  );
}
