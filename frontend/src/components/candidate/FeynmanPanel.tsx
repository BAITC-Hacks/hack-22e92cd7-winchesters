import type { FeynmanScore } from "@/lib/types";
import { ScoreBar } from "../ui/ScoreBar";
import { DarkPanel, Section } from "../ui/Section";

export function FeynmanPanel({ score }: { score: FeynmanScore }) {
  const rows: [string, number][] = [
    ["Overall", score.overall_score],
    ["Clarity", score.clarity],
    ["Patience", score.patience],
    ["Empathy", score.empathy],
    ["Adaptability", score.adaptability],
    ["Quiz Transfer", score.quiz_transfer_score],
  ];
  return (
    <Section title="Feynman Teaching Challenge">
      <DarkPanel className="space-y-3 text-sm">
        {rows.map(([label, value]) => (
          <div key={label} className="flex items-center gap-3">
            <span className="text-gray-300 w-28">{label}</span>
            <ScoreBar score={value} dark />
          </div>
        ))}
        <p className="text-gray-400 mt-3">{score.summary}</p>
      </DarkPanel>
    </Section>
  );
}
