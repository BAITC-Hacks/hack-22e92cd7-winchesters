"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import type { Competency, Level, OverrideEntry, OverrideInput, ReasonCodeOption } from "./types";

export interface OverridesState {
  /** Oldest first. null while loading. */
  history: OverrideEntry[] | null;
  reasonCodes: ReasonCodeOption[];
  error: string | null;
  /** Resolves to an error message to show, or null once recorded. */
  create: (input: OverrideInput) => Promise<string | null>;
}

/** One candidate's override ledger: loaded once, appended to on each override. */
export function useOverrides(candidateId: string): OverridesState {
  const [history, setHistory] = useState<OverrideEntry[] | null>(null);
  const [reasonCodes, setReasonCodes] = useState<ReasonCodeOption[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    Promise.all([api.overrides.list(candidateId), api.overrides.reasonCodes()])
      .then(([h, codes]) => {
        if (!live) return;
        setHistory(h.overrides);
        setReasonCodes(codes);
      })
      .catch((e) => {
        if (live) setError(e instanceof Error ? e.message : "Failed to load overrides");
      });
    return () => {
      live = false;
    };
  }, [candidateId]);

  const create = useCallback(
    async (input: OverrideInput) => {
      try {
        const entry = await api.overrides.create(candidateId, input);
        setHistory((prev) => [...(prev ?? []), entry]);
        return null;
      } catch (e) {
        return e instanceof Error ? e.message : "Override failed";
      }
    },
    [candidateId],
  );

  return { history, reasonCodes, error, create };
}

/** The committee's current level for a competency: the latest override, if any. */
export function committeeLevel(history: OverrideEntry[] | null, competency: Competency): Level | undefined {
  return history?.filter((o) => o.competency === competency).at(-1)?.to_level;
}
