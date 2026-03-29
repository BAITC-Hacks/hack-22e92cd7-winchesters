const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchJSON<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...opts,
    headers: { "Content-Type": "application/json", ...opts?.headers },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

import type {
  Candidate,
  CandidateScore,
  RankedCandidate,
  AIDetectionResult,
  ComparisonResult,
} from "./types";

export const api = {
  candidates: {
    list: () => fetchJSON<Candidate[]>("/api/candidates/"),
    get: (id: string) => fetchJSON<Candidate>(`/api/candidates/${id}`),
    create: (data: Omit<Candidate, "id">) =>
      fetchJSON<Candidate>("/api/candidates/", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },
  scoring: {
    baseline: (id: string) =>
      fetchJSON<CandidateScore>(`/api/scoring/baseline/${id}`, {
        method: "POST",
      }),
    baselineAll: () =>
      fetchJSON<CandidateScore[]>("/api/scoring/baseline/all", {
        method: "POST",
      }),
    ai: (id: string) =>
      fetchJSON<CandidateScore>(`/api/scoring/ai/${id}`, { method: "POST" }),
    rank: (scorer: string = "baseline") =>
      fetchJSON<RankedCandidate[]>(
        `/api/scoring/rank?scorer=${scorer}`,
        { method: "POST" }
      ),
    compare: (id: string) =>
      fetchJSON<ComparisonResult>(`/api/scoring/compare/${id}`),
    override: (candidateId: string, dimension: string, score: number, note: string) =>
      fetchJSON<CandidateScore>("/api/scoring/override", {
        method: "POST",
        body: JSON.stringify({
          candidate_id: candidateId,
          dimension,
          override_score: score,
          note,
        }),
      }),
  },
  analysis: {
    detectAI: (id: string) =>
      fetchJSON<AIDetectionResult>(`/api/analysis/ai-detection/${id}`, {
        method: "POST",
      }),
  },
};
