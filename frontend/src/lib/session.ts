// Where the login lives in the browser. One place for the keys, so logout,
// an expired token and a fresh login all clear the same set.

export interface User {
  id: string;
  email: string;
  full_name: string;
  candidate_id: string | null;
  role: Role;
}

export type Role = "applicant" | "interviewer" | "committee" | "admin";

export const STAFF_ROLES: Role[] = ["interviewer", "committee", "admin"];

const TOKEN_KEY = "invisionu_token";
const USER_KEY = "invisionu_user";
// Read by the application form and the teaching challenge.
const CANDIDATE_ID_KEY = "invisionu_candidate_id";
const CANDIDATE_NAME_KEY = "invisionu_candidate_name";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

/** The stored user as its raw JSON: a stable value for useSyncExternalStore. */
export function getStoredUserJSON(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(USER_KEY);
}

export function parseUser(raw: string | null): User | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

// localStorage only announces changes to other tabs; this event tells the
// components in this one.
const SESSION_EVENT = "invisionu-session";

export function subscribeToSession(onChange: () => void): () => void {
  window.addEventListener("storage", onChange);
  window.addEventListener(SESSION_EVENT, onChange);
  return () => {
    window.removeEventListener("storage", onChange);
    window.removeEventListener(SESSION_EVENT, onChange);
  };
}

function announce() {
  window.dispatchEvent(new Event(SESSION_EVENT));
}

export function saveSession(token: string, user: User) {
  localStorage.setItem(TOKEN_KEY, token);
  saveUser(user);
}

export function saveUser(user: User) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  localStorage.setItem(CANDIDATE_NAME_KEY, user.full_name);
  if (user.candidate_id) localStorage.setItem(CANDIDATE_ID_KEY, user.candidate_id);
  else localStorage.removeItem(CANDIDATE_ID_KEY);
  announce();
}

export function clearSession() {
  for (const key of [TOKEN_KEY, USER_KEY, CANDIDATE_ID_KEY, CANDIDATE_NAME_KEY]) {
    localStorage.removeItem(key);
  }
  announce();
}

/** Where a user lands after login, or when they open a page not meant for them.
 * Interviewers have no page of their own until the pre-brief (COM-03). */
export function homeFor(role: Role): string {
  return role === "committee" || role === "admin" ? "/dashboard" : "/";
}

/** Send the browser to the login page, remembering where it was. */
export function redirectToLogin() {
  if (typeof window === "undefined" || window.location.pathname === "/auth") return;
  const next = window.location.pathname + window.location.hash;
  window.location.href = `/auth?next=${encodeURIComponent(next)}`;
}
