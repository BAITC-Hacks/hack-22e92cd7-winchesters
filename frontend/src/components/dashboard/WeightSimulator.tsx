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
      icon="/assets/Settings.svg"
      title="Evaluation Settings"
      badge={
        !isDefault && (
          <span className="text-xs bg-[#c1f11d] text-[#141414] px-2.5 py-1 rounded-full font-medium">Custom weights active</span>
        )
      }
    >
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
    </CollapsiblePanel>
  );
}
