"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { DemoTranscript, FeynmanScore } from "@/lib/types";
import { ScoreBar } from "../ui/ScoreBar";
import { DarkPanel, Section } from "../ui/Section";
import { CachedDemoNotice, SimulationLabel, Transcript } from "../simulation/SimulationLabels";

function ScoreRows({ score }: { score: FeynmanScore }) {
  const rows: [string, number][] = [
    ["Overall", score.overall_score],
    ["Clarity", score.clarity],
    ["Patience", score.patience],
    ["Empathy", score.empathy],
    ["Adaptability", score.adaptability],
    ["Quiz Transfer", score.quiz_transfer_score],
  ];
  return (
    <DarkPanel className="space-y-3 text-sm">
      {rows.map(([label, value]) => (
        <div key={label} className="flex items-center gap-3">
          <span className="text-ink-3 w-28">{label}</span>
          <ScoreBar score={value} dark />
        </div>
      ))}
      <p className="text-ink-3 mt-3">{score.summary}</p>
    </DarkPanel>
  );
}

/**
 * Teaching Challenge / Scenario Lab result. With no session on file the
 * committee can open the cached demo transcript, which is labelled as such
 * and never attributed to this applicant.
 */
export function FeynmanPanel({ score }: { score: FeynmanScore | null }) {
  const [demo, setDemo] = useState<DemoTranscript | null>(null);
  const [demoError, setDemoError] = useState<string | null>(null);

  function openDemo() {
    setDemoError(null);
    api.feynman
      .demo()
      .then(setDemo)
      .catch((e) => setDemoError(e instanceof Error ? e.message : "Could not load the cached demo transcript."));
  }

  const title = score?.kind === "scenario" ? "Scenario Lab" : "Teaching Challenge / Scenario Lab";

  return (
    <Section title={title}>
      <div className="space-y-3">
        <SimulationLabel cached={score?.source === "cached_demo"} />
        {score ? (
          <ScoreRows score={score} />
        ) : (
          <div className="rounded-2xl border border-line bg-subtle px-4 py-3 text-sm text-ink-2">
            <p>No simulation session on file for this applicant.</p>
            {!demo && (
              <button
                type="button"
                onClick={openDemo}
                className="mt-2 px-3 py-1.5 rounded-[8px] bg-muted text-ink text-xs font-medium hover:bg-line"
              >
                Show cached demo transcript
              </button>
            )}
            {demoError && <p className="mt-2 text-danger">{demoError}</p>}
          </div>
        )}
        {!score && demo && (
          <div className="space-y-3">
            <CachedDemoNotice demo={demo} />
            <SimulationLabel cached />
            <p className="text-sm text-ink-2">
              <span className="font-semibold text-ink">{demo.topic.title}.</span> Not this applicant&apos;s session.
            </p>
            <Transcript messages={demo.messages} />
            <ScoreRows score={demo.score} />
          </div>
        )}
      </div>
    </Section>
  );
}
