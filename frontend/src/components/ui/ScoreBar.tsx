/** A 0–max bar with the value printed beside it. `dark` is for the gradient panels. */
export function ScoreBar({ score, max = 100, dark = false }: { score: number; max?: number; dark?: boolean }) {
  const pct = Math.min((score / max) * 100, 100);
  return (
    <div className="flex items-center gap-3 w-full">
      <div className={`flex-1 h-3 rounded-full overflow-hidden ${dark ? "bg-[#333]" : "bg-muted"}`}>
        <div
          className={`h-full rounded-full ${dark ? "bg-accent" : "bg-ink-2"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`text-sm font-mono w-9 text-right ${dark ? "text-ink-3" : ""}`}>{score.toFixed(0)}</span>
    </div>
  );
}
