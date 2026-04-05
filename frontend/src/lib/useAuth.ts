"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export interface User {
  id: string;
  email: string;
  full_name: string;
  candidate_id: string | null;
  role: string;
}

export function useAuth(requireAuth = true) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem("invisionu_token");
    const storedUser = localStorage.getItem("invisionu_user");

    if (storedToken && storedUser) {
      try {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      } catch {
        // Invalid stored data
        localStorage.removeItem("invisionu_token");
        localStorage.removeItem("invisionu_user");
      }
    }

    // Auth redirect disabled for development — enable when ready
    // if (requireAuth && !storedToken) {
    //   router.push("/auth");
    // }

    setLoading(false);
  }, [requireAuth, router]);

  function logout() {
    localStorage.removeItem("invisionu_token");
    localStorage.removeItem("invisionu_user");
    localStorage.removeItem("invisionu_candidate_id");
    localStorage.removeItem("invisionu_candidate_name");
    setUser(null);
    setToken(null);
    router.push("/auth");
  }

  function updateUser(updates: Partial<User>) {
    if (!user) return;
    const updated = { ...user, ...updates };
    setUser(updated);
    localStorage.setItem("invisionu_user", JSON.stringify(updated));
  }

  return { user, token, loading, logout, updateUser };
}
