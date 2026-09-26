import type {
  Candidate,
  CandidateLedger,
  CandidateScore,
  CounterfactualProbeResult,
  CohortProbeReport,
  FairnessAuditReport,
  EvaluationReport,
  ModelCard,
  HeldoutReport,
  FunderMemo,
  HeldoutReproducibility,
  OverrideEntry,
  OverrideInput,
  RankedCandidate,
  ReasonCodeOption,
  AIDetectionResult,
  VideoAnalysis,
  CommitteeDecisionMemo,
} from "./types";
import { parseLedger } from "./ledger";
import ledgerFixture from "./fixtures/ledger_example.json";
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

async function fetchPDF(path: string): Promise<Blob> {
  const token = getToken();
  const res = await fetch(`${API}${path}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
  if (!res.ok) throw new ApiError(res.status, detailOf(await res.text()));
  return res.blob();
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
  },
  // Committee overrides of a competency level (COM-01). Append-only: there is
  // no edit or delete, only a new override on top.
  overrides: {
    reasonCodes: () => fetchJSON<ReasonCodeOption[]>("/api/overrides/reason-codes"),
    list: (candidateId: string) =>
      fetchJSON<{ candidate_id: string; overrides: OverrideEntry[] }>(
        `/api/overrides/${encodeURIComponent(candidateId)}`,
      ),
    create: (candidateId: string, input: OverrideInput) =>
      fetchJSON<OverrideEntry>(`/api/overrides/${encodeURIComponent(candidateId)}`, {
        method: "POST",
        body: JSON.stringify(input),
      }),
  },
  // Attribute-grouped audit (FAIR-07), committee and admin only. "synthetic"
  // until LED-11 stores real levels; "db" is empty before then.
  fairness: {
    audit: (source: "synthetic" | "db" = "synthetic") =>
      fetchJSON<FairnessAuditReport>(`/api/fairness/audit?source=${source}`),
    probe: (candidateId: string, live = true) =>
      fetchJSON<CounterfactualProbeResult>(
        `/api/fairness/probe/${encodeURIComponent(candidateId)}?live=${live}`,
        { method: "POST" },
      ),
      evaluation: (live = false) => fetchJSON<EvaluationReport>(`/api/fairness/evaluation?live=${live}`),
      cohortProbe: (live = false) => fetchJSON<CohortProbeReport>(`/api/fairness/cohort-probe?live=${live}`),
      modelCard: () => fetchJSON<ModelCard>("/api/fairness/historical/model-card"),
      heldoutReport: () => fetchJSON<HeldoutReport>("/api/fairness/heldout/report"),
      funderMemo: () => fetchJSON<FunderMemo>("/api/fairness/heldout/memo"),
      heldoutReproduce: () => fetchJSON<HeldoutReproducibility>("/api/fairness/heldout/reproduce"),
  },
  committee: {
    decisionMemo: (candidateId: string) => fetchJSON<CommitteeDecisionMemo>(`/api/committee/decision-memo/${encodeURIComponent(candidateId)}`),
    decisionMemoPdf: (candidateId: string) => fetchPDF(`/api/committee/decision-memo/${encodeURIComponent(candidateId)}/pdf`),
  },
  analysis: {
    detectAI: (id: string) =>
      fetchJSON<AIDetectionResult>(`/api/analysis/ai-detection/${id}`, {
        method: "POST",
      }),
    analyzeVideo: (id: string) =>
      fetchJSON<VideoAnalysis>(`/api/analysis/video-analysis/${id}`, {
        method: "POST",
      }),
  },
  // Until LED-11 there is no ledger API: every candidate gets the LED-03
  // worked example. The async signature is the one LED-11 keeps, so only these
  // two bodies change when `routers/ledger.py` lands.
  ledger: {
    get: async (candidateId: string): Promise<CandidateLedger> => {
      void candidateId; // the fixture is one pseudonymous applicant, shown for everyone
      return parseLedger(ledgerFixture);
    },
    list: async (): Promise<CandidateLedger[]> => [parseLedger(ledgerFixture)],
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

