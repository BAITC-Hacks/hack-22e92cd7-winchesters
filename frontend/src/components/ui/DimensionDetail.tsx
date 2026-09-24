"use client";

import { useState } from "react";
import { DIMENSION_LABELS } from "@/lib/dashboard";
import type { DimensionScore } from "@/lib/types";
import { Badge } from "./Badge";
import { ScoreBar } from "./ScoreBar";

/** One scored dimension, expandable to its explanation, quotes and factors. */
export function DimensionDetail({ dim, weight }: { dim: DimensionScore; weight: number }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-gray-200 last:border-0 py-3">
      <button className="w-full flex items-center justify-between text-left" onClick={() => setOpen(!open)}>
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-1">
            <span className="text-base font-medium text-gray-800">
              {DIMENSION_LABELS[dim.dimension] || dim.dimension}
            </span>
            <span className="text-xs text-gray-400">{(weight * 100).toFixed(0)}%</span>
            <Badge
              label={dim.confidence}
              color={dim.confidence === "high" ? "green" : dim.confidence === "medium" ? "yellow" : "red"}
            />
          </div>
          <ScoreBar score={dim.score} />
        </div>
        <span className="ml-3 text-gray-400 text-sm">{open ? "−" : "+"}</span>
      </button>
      {open && (
        <div className="mt-3 pl-3 text-sm space-y-3">
          <p className="text-gray-600">{dim.explanation}</p>
          {dim.evidence_quotes.length > 0 && (
            <div>
              <p className="font-medium text-gray-500 mb-1">Evidence:</p>
              {dim.evidence_quotes.map((q, i) => (
                <blockquote key={i} className="border-l-2 border-[#c1f11d] pl-3 text-gray-500 italic mb-1">
                  &ldquo;{q}&rdquo;
                </blockquote>
              ))}
            </div>
          )}
          {dim.positive_factors.length > 0 && (
            <div>
              <p className="font-medium text-[#141414] mb-1">Strengths:</p>
              <ul className="list-disc list-inside text-gray-600">
                {dim.positive_factors.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </div>
          )}
          {dim.concerns.length > 0 && (
            <div>
              <p className="font-medium text-red-600 mb-1">Concerns:</p>
              <ul className="list-disc list-inside text-gray-600">
                {dim.concerns.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
