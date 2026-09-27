import type { DemoTranscript, FeynmanTopic } from "@/lib/types";

/**
 * The label every simulation result carries (INP-03): it was observed in a
 * simulation, and it has weight zero in every score and ranking. `cached`
 * adds that the transcript is the checked-in demo, not a live session.
 */
export function SimulationLabel({ cached = false, className = "" }: { cached?: boolean; className?: string }) {
  return (
    <div className={`flex flex-wrap items-center gap-1.5 ${className}`}>
      <span className="inline-block px-2 py-0.5 rounded-[6px] bg-muted text-ink text-xs font-medium">
        Observed in simulation
      </span>
      <span className="inline-block px-2 py-0.5 rounded-[6px] bg-subtle border border-line text-ink-2 text-xs">
        Weight 0: not part of any score or ranking
      </span>
      {cached && (
        <span className="inline-block px-2 py-0.5 rounded-[6px] bg-accent-soft text-accent-ink text-xs font-semibold uppercase tracking-wide">
          Cached demo transcript
        </span>
      )}
    </div>
  );
}

/** Scenario wording is ours until Talent Craft sends the methodology. */
export function ProvisionalChip({ topic }: { topic: Pick<FeynmanTopic, "status" | "status_note"> }) {
  if (topic.status !== "provisional") return null;
  return (
    <span
      className="inline-block px-2 py-0.5 rounded-[6px] border border-line text-warn-ink text-xs font-medium"
      title={topic.status_note}
    >
      Provisional wording
    </span>
  );
}

/** Banner above a replayed transcript: what it is and where it came from. */
export function CachedDemoNotice({ demo, reason }: { demo: DemoTranscript; reason?: string | null }) {
  return (
    <div className="rounded-2xl border border-line bg-subtle px-4 py-3 text-sm text-ink-2 space-y-1">
      <p className="font-semibold text-ink">
        Cached demo transcript: replayed from a fixture, not a live session.
      </p>
      {reason && <p>{reason}</p>}
      <p className="text-ink-3">{demo.provenance}</p>
    </div>
  );
}

export function Transcript({ messages }: { messages: DemoTranscript["messages"] }) {
  return (
    <div className="flex flex-col gap-3">
      {messages.map((m, i) => (
        <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
          <div
            className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
              m.role === "user" ? "bg-accent text-ink" : "bg-subtle border border-line text-ink"
            }`}
          >
            <p className="text-xs font-semibold text-ink-2 mb-1">{m.role === "user" ? "Candidate" : "Arman (AI, 10 y.o.)"}</p>
            {m.content}
          </div>
        </div>
      ))}
    </div>
  );
}
