import type { VideoAnalysis } from "@/lib/types";
import { ScoreBar } from "../ui/ScoreBar";
import { Section } from "../ui/Section";

// INP-01: a result without a transcript, or without a model, carries no
// numbers, so it is shown as a neutral notice, never as zeros or "weak".
const NOTICE: Record<Exclude<VideoAnalysis["status"], "analyzed">, string> = {
  no_transcript: "No transcript — nothing was scored.",
  unavailable: "Analysis unavailable — nothing was scored.",
};

function Chips({ label, items }: { label: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div className="mb-2">
      <span className="text-xs text-ink-3">{label}: </span>
      {items.map((item, i) => (
        <span key={i} className="inline-block rounded-lg bg-muted text-ink-2 text-xs px-2 py-0.5 mr-1 my-0.5">
          {item}
        </span>
      ))}
    </div>
  );
}

export function VideoPanel({ analysis, onRun }: { analysis: VideoAnalysis | null; onRun: () => void }) {
  return (
    <Section title="Video Presentation Analysis">
      {!analysis ? (
        <button
          className="rounded-xl bg-ink text-accent px-5 py-2.5 text-sm font-semibold hover:opacity-90 transition"
          onClick={onRun}
        >
          Analyze Video Presentation
        </button>
      ) : analysis.status !== "analyzed" ? (
        <div data-video-status={analysis.status} className="rounded-2xl border border-line bg-subtle px-5 py-4">
          <p className="text-sm font-medium text-ink">{NOTICE[analysis.status]}</p>
          <p className="text-xs text-ink-3 mt-1">
            The written presentation is the scored input. A video transcript is auxiliary and is only analysed when the
            applicant&apos;s own transcript exists.
          </p>
        </div>
      ) : (
        <div data-video-status="analyzed" className="rounded-2xl border border-line bg-surface p-5">
          {analysis.authenticity_match !== null && (
            <div className="flex items-center gap-3 mb-3">
              <span className="text-sm text-ink-2 whitespace-nowrap">Authenticity Match:</span>
              <ScoreBar score={analysis.authenticity_match} />
            </div>
          )}
          {analysis.motivation_score !== null && (
            <div className="flex items-center gap-3 mb-3">
              <span className="text-sm text-ink-2 whitespace-nowrap">Motivation Score:</span>
              <ScoreBar score={analysis.motivation_score} />
            </div>
          )}
          <p className="text-sm text-ink-2 leading-relaxed mb-3">{analysis.summary}</p>
          <Chips label="Key themes" items={analysis.key_themes} />
          <Chips label="Growth signals" items={analysis.growth_signals} />
          <Chips label="Concerns" items={analysis.concerns} />
        </div>
      )}
    </Section>
  );
}
