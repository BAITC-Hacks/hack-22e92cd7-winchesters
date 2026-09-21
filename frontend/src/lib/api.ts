import type {
  Candidate,
  CandidateScore,
  RankedCandidate,
  AIDetectionResult,
} from "./types";
import { clearSession, getToken, redirectToLogin, type User } from "./session";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

/** FastAPI's `detail` as text: a string, or the first validation message. */
function detailOf(body: string): string {
  try {
    const detail = JSON.parse(body).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
  } catch {
    /* not JSON */
  }
  return body;
}

// Every request carries the stored token. A 401 means it is missing, expired
// or revoked: the session is dropped and the user sent to log in again. Login
// itself is exempt, where a 401 just means a wrong password.
async function fetchJSON<T>(path: string, opts?: RequestInit & { anonymous?: boolean }): Promise<T> {
  const token = opts?.anonymous ? null : getToken();
  const res = await fetch(`${API}${path}`, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...opts?.headers,
    },
  });
  if (!res.ok) {
    const detail = detailOf(await res.text());
    if (res.status === 401 && !opts?.anonymous) {
      clearSession();
      redirectToLogin();
      throw new ApiError(401, "Your session has expired. Please sign in again.");
    }
    if (res.status === 403) {
      throw new ApiError(403, `You don't have access to this: ${detail}`);
    }
    throw new ApiError(res.status, detail || `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  auth: {
    register: (email: string, password: string, full_name: string) =>
      fetchJSON<{ token: string; user: User }>("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password, full_name }),
        anonymous: true,
      }),
    login: (email: string, password: string) =>
      fetchJSON<{ token: string; user: User }>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
        anonymous: true,
      }),
    me: () => fetchJSON<User>("/api/auth/me"),
    // Submitting an application already links it; this only confirms the link.
    linkCandidate: (candidateId: string) =>
      fetchJSON<{ status: string; candidate_id: string }>(
        `/api/auth/link-candidate?candidate_id=${encodeURIComponent(candidateId)}`,
        { method: "POST" },
      ),
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
    score: <T>(candidateId: string) =>
      fetchJSON<T | null>(`/api/feynman/score/${encodeURIComponent(candidateId)}`),
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
