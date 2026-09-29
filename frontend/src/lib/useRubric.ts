"use client";

import { useEffect, useState } from "react";
import { api } from "./api";
import type { RubricStatus } from "./types";

// One request per page load: every view that needs indicator names shares it.
let pending: Promise<RubricStatus | null> | null = null;

/** The rubric the server has now, or null while loading or when it cannot be read. */
export function useRubric(): RubricStatus | null {
  const [rubric, setRubric] = useState<RubricStatus | null>(null);
  useEffect(() => {
    pending ??= api.ledger.rubric().catch(() => null);
    let live = true;
    pending.then((r) => live && setRubric(r));
    return () => {
      live = false;
    };
  }, []);
  return rubric;
}

/** Indicator id -> readable name, e.g. "lead.initiative" -> "Initiative". */
export function indicatorLabels(rubric: RubricStatus | null): Map<string, string> {
  return new Map(rubric?.competencies.flatMap((c) => c.indicators.map((i) => [i.id, i.label] as const)) ?? []);
}
