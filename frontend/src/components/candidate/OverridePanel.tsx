"use client";

import { useState } from "react";
import { DIMENSION_LABELS } from "@/lib/dashboard";
import type { CandidateScore } from "@/lib/types";
import { Section } from "../ui/Section";

/**
 * The legacy per-dimension override form. Since FND-04 PR 3 the endpoint answers
 * 410 until the override ledger (COM-01) exists; the backend's message is shown
 * and the form locks, instead of the old silent no-op.
 */
export function OverridePanel({
  score,
  onOverride,
}: {
  score: CandidateScore;
  /** Resolves to an error message to show, or null on success. */
  onOverride: (dimension: string, value: number, note: string) => Promise<string | null>;
}) {
  const [overrideDim, setOverrideDim] = useState("");
  const [overrideVal, setOverrideVal] = useState(50);
  const [overrideNote, setOverrideNote] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [locked, setLocked] = useState(false);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setBusy(true);
    const error = await onOverride(overrideDim, overrideVal, overrideNote);
    setBusy(false);
    setMessage(error);
    if (error) {
      setLocked(true);
    } else {
      setOverrideDim("");
      setOverrideNote("");
    }
  };

  return (
    <Section title="Committee Override">
      <fieldset disabled={locked || busy} className="bg-[#eae9e9] rounded-2xl p-5 space-y-4 disabled:opacity-70">
        {message && (
          <p role="alert" className="text-sm text-[#141414] bg-white border-2 border-[#141414] rounded-xl px-4 py-3">
            {message}
          </p>
        )}
        <select
          className="w-full border border-gray-300 rounded-xl px-4 py-2.5 text-base bg-white focus:border-[#c1f11d] focus:ring-1 focus:ring-[#c1f11d] outline-none"
          value={overrideDim}
          onChange={(e) => setOverrideDim(e.target.value)}
        >
          <option value="">Select dimension...</option>
          {score.dimensions.map((d) => (
            <option key={d.dimension} value={d.dimension}>
              {DIMENSION_LABELS[d.dimension] || d.dimension} (current: {d.score.toFixed(0)})
            </option>
          ))}
        </select>
        <div className="flex items-center gap-3">
          <input
            type="range"
            min={0}
            max={100}
            value={overrideVal}
            onChange={(e) => setOverrideVal(Number(e.target.value))}
            className="flex-1 accent-[#c1f11d]"
          />
          <span className="text-base font-mono w-9">{overrideVal}</span>
        </div>
        <input
          type="text"
          placeholder="Note (reason for override)"
          className="w-full border border-gray-300 rounded-xl px-4 py-2.5 text-base bg-white focus:border-[#c1f11d] focus:ring-1 focus:ring-[#c1f11d] outline-none"
          value={overrideNote}
          onChange={(e) => setOverrideNote(e.target.value)}
        />
        <button
          className="px-5 py-2.5 bg-[#c1f11d] text-[#141414] rounded-xl text-base font-semibold hover:scale-105 transition-transform disabled:opacity-50"
          disabled={!overrideDim || locked || busy}
          onClick={submit}
        >
          {busy ? "Applying..." : "Apply Override"}
        </button>
      </fieldset>
    </Section>
  );
}
