import type { VideoAnalysis } from "@/lib/types";
import { ScoreBar } from "../ui/ScoreBar";
import { Section } from "../ui/Section";

const chip = (bg: string, fg: string) => ({
  display: "inline-block",
  backgroundColor: bg,
  color: fg,
  borderRadius: "8px",
  padding: "2px 8px",
  fontSize: "11px",
  margin: "2px 4px 2px 0",
});

export function VideoPanel({ analysis, onRun }: { analysis: VideoAnalysis | null; onRun: () => void }) {
  return (
    <Section title="Video Presentation Analysis">
      {analysis ? (
        <div style={{ background: "linear-gradient(180deg, #252525, #0F0F0F)", borderRadius: "16px", padding: "20px", border: "1px solid #333" }}>
          {analysis.is_mock && (
            <div style={{ backgroundColor: "rgba(193,241,29,0.1)", borderRadius: "8px", padding: "8px 12px", marginBottom: "12px", fontSize: "12px", color: "#c1f11d" }}>
              Demo mode — using mock transcript. Add OPENAI_API_KEY for real Whisper transcription.
            </div>
          )}
          <div className="flex items-center gap-3 mb-3">
            <span style={{ color: "#999", fontSize: "13px" }}>Authenticity Match:</span>
            <ScoreBar score={analysis.authenticity_match} dark />
          </div>
          <div className="flex items-center gap-3 mb-3">
            <span style={{ color: "#999", fontSize: "13px" }}>Motivation Score:</span>
            <ScoreBar score={analysis.motivation_score} dark />
          </div>
          <p style={{ color: "#ccc", fontSize: "13px", lineHeight: 1.6, marginBottom: "12px" }}>{analysis.summary}</p>
          {analysis.key_themes.length > 0 && (
            <div style={{ marginBottom: "8px" }}>
              <span style={{ color: "#999", fontSize: "12px" }}>Key themes: </span>
              {analysis.key_themes.map((t, i) => (
                <span key={i} style={chip("rgba(193,241,29,0.15)", "#c1f11d")}>{t}</span>
              ))}
            </div>
          )}
          {analysis.growth_signals.length > 0 && (
            <div style={{ marginBottom: "8px" }}>
              <span style={{ color: "#999", fontSize: "12px" }}>Growth signals: </span>
              {analysis.growth_signals.map((g, i) => (
                <span key={i} style={chip("rgba(16,185,129,0.15)", "#10b981")}>{g}</span>
              ))}
            </div>
          )}
          {analysis.concerns.length > 0 && (
            <div>
              <span style={{ color: "#999", fontSize: "12px" }}>Concerns: </span>
              {analysis.concerns.map((c, i) => (
                <span key={i} style={chip("rgba(239,68,68,0.15)", "#ef4444")}>{c}</span>
              ))}
            </div>
          )}
        </div>
      ) : (
        <button
          style={{ backgroundColor: "#141414", color: "#c1f11d", border: "none", borderRadius: "12px", padding: "10px 20px", fontSize: "14px", fontWeight: 600, cursor: "pointer" }}
          onClick={onRun}
        >
          Analyze Video Presentation
        </button>
      )}
    </Section>
  );
}
