"use client";

import { EvaluationHarness } from "@/components/fairness/EvaluationHarness";
import { useAuth } from "@/lib/useAuth";

export default function EvaluationPage() {
  const { ready } = useAuth({ requireAuth: true, roles: ["committee", "admin"] });
  if (!ready) return <main className="p-8 text-sm text-[#5d5d5d]">Checking access...</main>;
  return <EvaluationHarness />;
}
