import { DEFAULT_WEIGHTS, DIMENSION_KEYS, DIMENSION_LABELS } from "@/lib/dashboard";
import { CollapsiblePanel } from "../ui/CollapsiblePanel";

export function WeightSimulator({
  weights,
  onChange,
  onReset,
}: {
  weights: Record<string, number>;
  onChange: (key: string, value: number) => void;
  onReset: () => void;
}) {
  const total = Object.values(weights).reduce((a, b) => a + b, 0);
  const isDefault = DIMENSION_KEYS.every((k) => Math.abs(weights[k] - DEFAULT_WEIGHTS[k]) < 0.001);

  return (
    <CollapsiblePanel
      icon="/assets/icons/settings.svg"
      title="Evaluation Settings"
      badge={
        !isDefault && (
          <span className="text-xs bg-accent text-ink px-2.5 py-1 rounded-full font-medium">Custom weights active</span>
        )
      }
    >
      <p className="mb-5 text-sm text-ink-2">
        How much each dimension counts toward the order of the list. The list reorders live.
      </p>
      <div className="space-y-4">
        {DIMENSION_KEYS.map((key) => (
          <div key={key} className="flex items-center gap-3">
            <span className="w-[120px] text-sm text-ink-2">{DIMENSION_LABELS[key]}</span>
            <input
              type="range"
              min={0}
              max={50}
              value={Math.round(weights[key] * 100)}
              onChange={(e) => onChange(key, parseInt(e.target.value) / 100)}
              className="h-2 flex-1 accent-ink"
            />
            <span className="w-12 text-right font-mono text-sm text-ink">
              {Math.round(weights[key] * 100)}%
            </span>
          </div>
        ))}
      </div>
      <div className="mt-5 flex items-center justify-between border-t border-line-soft pt-4">
        <span className={`text-sm ${Math.abs(total - 1) > 0.01 ? "text-danger" : "text-ink-3"}`}>
          Total: {Math.round(total * 100)}%{Math.abs(total - 1) > 0.01 && " (should be 100%)"}
        </span>
        {!isDefault && (
          <button type="button" onClick={onReset} className="rounded-full border border-line px-3.5 py-1.5 text-sm font-semibold text-ink hover:border-ink">
            Reset to defaults
          </button>
        )}
      </div>
    </CollapsiblePanel>
  );
}
