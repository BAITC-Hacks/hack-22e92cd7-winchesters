import type { Scenario, ScenarioMessage } from "@/lib/types";

/**
 * The label every scenario result carries: it was observed in a simulation,
 * and it has weight zero, so it never changes the AI level, a rank or a
 * recommendation. `demo` adds that the partner followed a script.
 */
export function SimulationLabel({ demo = false, className = "" }: { demo?: boolean; className?: string }) {
  return (
    <div className={`flex flex-wrap items-center gap-1.5 ${className}`}>
      <span className="inline-block rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium text-ink">Observed in simulation</span>
      <span className="inline-block rounded-full border border-line px-2.5 py-0.5 text-xs text-ink-2">
        Weight 0: not part of any score or ranking
      </span>
      {demo && (
        <span className="inline-block rounded-full border border-line px-2.5 py-0.5 text-xs text-ink-3">
          Demo mode · scripted partner
        </span>
      )}
    </div>
  );
}

/** Scenario wording is ours until Talent Craft sends the methodology. */
export function ProvisionalChip({ scenario }: { scenario: Pick<Scenario, "status" | "status_note"> }) {
  if (scenario.status !== "provisional") return null;
  return (
    <span className="inline-block rounded-full border border-line px-2.5 py-0.5 text-xs font-medium text-warn-ink" title={scenario.status_note}>
      Provisional wording
    </span>
  );
}

export function Transcript({ messages, partnerLabel }: { messages: ScenarioMessage[]; partnerLabel: string }) {
  return (
    <div className="flex flex-col gap-3">
      {messages.map((m, i) => (
        <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
          <div
            className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-relaxed ${
              m.role === "user" ? "bg-accent text-ink" : "border border-line bg-subtle text-ink"
            }`}
          >
            <p className="mb-1 text-xs font-semibold text-ink-2">{m.role === "user" ? "Applicant" : partnerLabel}</p>
            {m.content}
          </div>
        </div>
      ))}
    </div>
  );
}
