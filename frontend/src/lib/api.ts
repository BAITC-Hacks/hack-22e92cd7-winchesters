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
} from "./types";

export const api = {
  auth: {
    register: (email: string, password: string, full_name: string) =>
      fetchJSON<{ token: string; user: { id: string; email: string; full_name: string; candidate_id: string | null; role: string } }>("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password, full_name }),
      }),
    login: (email: string, password: string) =>
      fetchJSON<{ token: string; user: { id: string; email: string; full_name: string; candidate_id: string | null; role: string } }>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
    me: (token: string) =>
      fetchJSON<{ id: string; email: string; full_name: string; candidate_id: string | null; role: string }>("/api/auth/me", {
        headers: { Authorization: `Bearer ${token}` },
      }),
    linkCandidate: (token: string, candidateId: string) =>
      fetchJSON<{ status: string; candidate_id: string }>(`/api/auth/link-candidate?candidate_id=${candidateId}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      }),
  },
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
    analyzeVideo: (id: string) =>
      fetchJSON<{
        transcript: string;
        language_detected: string;
        authenticity_match: number;
        motivation_score: number;
        key_themes: string[];
        growth_signals: string[];
        concerns: string[];
        summary: string;
        is_mock: boolean;
      }>(`/api/analysis/video-analysis/${id}`, {
        method: "POST",
      }),
  },
  feynman: {
    topics: () => fetchJSON<{ id: string; title: string; description: string }[]>("/api/feynman/topics"),
    start: (candidateId: string, topicId: string) =>
      fetchJSON<{ session_id: string; topic: { id: string; title: string; description: string }; first_message: string }>(
        "/api/feynman/start",
        { method: "POST", body: JSON.stringify({ candidate_id: candidateId, topic_id: topicId }) },
      ),
    chat: (sessionId: string, message: string) =>
      fetchJSON<{ reply: string; message_count: number; can_finish: boolean; must_finish: boolean; remaining: number }>(
        "/api/feynman/chat",
        { method: "POST", body: JSON.stringify({ session_id: sessionId, message }) },
      ),
    finish: (sessionId: string) =>
      fetchJSON<{
        session_id: string; candidate_id: string; topic_id: string;
        clarity: number; patience: number; empathy: number; adaptability: number;
        quiz_transfer_score: number; overall_score: number; summary: string; message_count: number;
      }>(`/api/feynman/finish?session_id=${sessionId}`, { method: "POST" }),
  },
};
