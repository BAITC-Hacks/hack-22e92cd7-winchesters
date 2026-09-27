"use client";

import { useCallback, useEffect, useMemo, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";
import { api } from "./api";
import {
  clearSession,
  getStoredUserJSON,
  getToken,
  homeFor,
  parseUser,
  redirectToLogin,
  saveUser,
  subscribeToSession,
  type Role,
  type User,
} from "./session";

export type { Role, User } from "./session";

interface Options {
  /** Send anonymous visitors to /auth. */
  requireAuth?: boolean;
  /** Roles allowed on this page; anyone else is sent to their own home page. */
  roles?: Role[];
}

const noSubscription = () => () => {};

/**
 * The logged-in user, read from localStorage and then confirmed with
 * /api/auth/me. An expired token fails that call, and the API client sends
 * the user to log in again. `ready` turns true only once access is settled,
 * so a page can wait for it before loading data it may not be allowed to see.
 */
export function useAuth({ requireAuth = false, roles }: Options = {}) {
  const router = useRouter();
  // The server has no localStorage: it renders "not loaded", and the client
  // fills the session in right after hydration.
  const hydrated = useSyncExternalStore(noSubscription, () => true, () => false);
  const token = useSyncExternalStore(subscribeToSession, getToken, () => null);
  const userJSON = useSyncExternalStore(subscribeToSession, getStoredUserJSON, () => null);
  const user = useMemo(() => (token ? parseUser(userJSON) : null), [token, userJSON]);

  const rolesKey = roles?.join(",") ?? "";
  const allowed = !user || !rolesKey || rolesKey.split(",").includes(user.role);

  useEffect(() => {
    if (!hydrated) return;
    if (!user) {
      if (requireAuth) redirectToLogin();
      return;
    }
    if (!allowed) router.replace(homeFor(user.role));
  }, [hydrated, user, allowed, requireAuth, router]);

  // Refresh from the server once per token: picks up a newly linked
  // application, and a 401 (expired token) logs the user out via the client.
  useEffect(() => {
    if (!token) return;
    api.auth.me().then(saveUser).catch(() => {});
  }, [token]);

  const logout = useCallback(() => {
    clearSession();
    router.push("/auth");
  }, [router]);

  const updateUser = useCallback(
    (updates: Partial<User>) => {
      if (user) saveUser({ ...user, ...updates });
    },
    [user],
  );

  const loading = !hydrated;
  const ready = hydrated && allowed && (!requireAuth || user !== null);
  return { user, token, loading, ready, logout, updateUser };
}
