"use client";

import { useState } from "react";
import type { Competency, Level, OverrideEntry, OverrideInput, ReasonCodeOption } from "@/lib/types";
import { LEVELS } from "@/lib/types";
import { LevelChip } from "./LevelChip";
import { STATE_LABELS } from "./labels";

// Placeholder styling until LED-06 delivers the card design. What must survive
// the redesign: the AI level stays visible next to the committee's, and an
// override cannot be sent without a reason code.

const FIELD =
  "border border-gray-300 rounded-xl px-3 py-2 text-sm bg-white focus:border-[#c1f11d] focus:ring-1 focus:ring-[#c1f11d] outline-none";

/** Inline form on a competency row. Records a new override; never edits one. */
export function OverrideForm({
  competency,
  current,
  aiLevel,
  reasonCodes,
  onSubmit,
  onDone,
}: {
  competency: Competency;
  /** The level the row currently shows (committee's, else AI's). */
  current: Level | null;
  aiLevel: Level | null;
  reasonCodes: ReasonCodeOption[];
  onSubmit: (input: OverrideInput) => Promise<string | null>;
  onDone: () => void;
}) {
  const [toLevel, setToLevel] = useState<Level | "">("");
  const [reasonCode, setReasonCode] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const noteRequired = reasonCodes.find((r) => r.code === reasonCode)?.note_required ?? false;

  const submit = async () => {
    if (!toLevel) return setError("Choose the new level.");
    if (toLevel === current) return setError(`This competency is already ${STATE_LABELS[toLevel]}.`);
    if (!reasonCode) return setError("Choose a reason code. An override without one is not recorded.");
    if (noteRequired && !note.trim()) return setError("This reason code needs a note.");
    setBusy(true);
    const failure = await onSubmit({ competency, to_level: toLevel, reason_code: reasonCode, note, ai_level: aiLevel });
    setBusy(false);
    if (failure) setError(failure);
    else onDone();
  };

  return (
    <fieldset
      disabled={busy}
      data-slot="override-form"
      className="mt-3 bg-[#eae9e9] rounded-2xl p-4 space-y-3 disabled:opacity-70"
    >
      <legend className="sr-only">Override level</legend>
      {error && (
        <p role="alert" className="text-sm text-[#141414] bg-white border-2 border-[#141414] rounded-xl px-3 py-2">
          {error}
        </p>
      )}
      <div className="flex flex-wrap gap-3">
        <label className="flex flex-col gap-1 text-xs text-[#5d5d5d]">
          New level
          <select className={FIELD} value={toLevel} onChange={(e) => setToLevel(e.target.value as Level | "")}>
            <option value="">Select level...</option>
            {LEVELS.map((l) => (
              <option key={l} value={l} disabled={l === current}>
                {STATE_LABELS[l]}
                {l === current ? " (current)" : ""}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-[#5d5d5d] flex-1 min-w-[14rem]">
          Reason code (required)
          <select
            className={FIELD}
            value={reasonCode}
            onChange={(e) => setReasonCode(e.target.value)}
            aria-required
          >
            <option value="">Select reason...</option>
            {reasonCodes.map((r) => (
              <option key={r.code} value={r.code}>
                {r.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      <label className="flex flex-col gap-1 text-xs text-[#5d5d5d]">
        Note{noteRequired ? " (required for this reason)" : " (optional)"}
        <input
          type="text"
          maxLength={1000}
          className={FIELD}
          placeholder="What the committee saw"
          value={note}
          onChange={(e) => setNote(e.target.value)}
        />
      </label>
      <div className="flex gap-2">
        <button
          className="px-4 py-2 bg-[#c1f11d] text-[#141414] rounded-xl text-sm font-semibold hover:scale-105 transition-transform"
          onClick={submit}
        >
          {busy ? "Recording..." : "Record override"}
        </button>
        <button className="px-4 py-2 rounded-xl text-sm text-[#5d5d5d] hover:text-[#141414]" onClick={onDone}>
          Cancel
        </button>
      </div>
      <p className="text-xs text-[#969696]">
        Overrides are append-only: the AI level stays on the card, and a later change is a new entry.
      </p>
    </fieldset>
  );
}

const when = (iso: string) => new Date(iso).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" });

/** Who changed this competency, from what, to what, when and why. Oldest first. */
export function OverrideHistory({ entries, reasonCodes }: { entries: OverrideEntry[]; reasonCodes: ReasonCodeOption[] }) {
  const labelOf = (code: string | null) =>
    code ? (reasonCodes.find((r) => r.code === code)?.label ?? code) : "No reason code";
  return (
    <ol data-slot="override-history" className="mt-3 space-y-2 border-l-2 border-[#d7d7d7] pl-3">
      {entries.map((o) => (
        <li key={o.id} className="text-sm">
          <div className="flex flex-wrap items-center gap-2">
            {o.from_level ? (
              <LevelChip state={o.from_level} small />
            ) : (
              <span className="text-xs text-[#969696]">No AI level</span>
            )}
            <span className="text-[#969696]">→</span>
            <LevelChip state={o.to_level} small />
            <span className="text-[#141414] font-medium">{labelOf(o.reason_code)}</span>
          </div>
          {o.note && <p className="text-[#5d5d5d] mt-0.5">“{o.note}”</p>}
          <p className="text-xs text-[#969696] mt-0.5">
            {o.author.full_name || "Unknown user"} ({o.author.role || "?"}) · {when(o.created_at)}
          </p>
        </li>
      ))}
    </ol>
  );
}
