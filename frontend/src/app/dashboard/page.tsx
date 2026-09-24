"use client";

// The admissions dashboard: loads data, holds selection and filter state, lays
// out the views. Rendering lives in src/components/.

import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { DEFAULT_WEIGHTS, groupOf, groupsFor, isHiddenGem, reweight, scoreOf, type Scorer } from "@/lib/dashboard";
import type { AIDetectionResult, CandidateLedger, FeynmanScore, RankedCandidate, VideoAnalysis } from "@/lib/types";
import { CandidateDetail } from "@/components/candidate/CandidateDetail";
import { CandidateCard } from "@/components/dashboard/CandidateCard";
import { DashboardFooter, DashboardHeader, DashboardNav, ScrollProgress } from "@/components/dashboard/Chrome";
import { Toolbar } from "@/components/dashboard/Toolbar";
import { WeightSimulator } from "@/components/dashboard/WeightSimulator";
import { FairnessAudit } from "@/components/views/FairnessAudit";

const ITEMS_PER_PAGE = 9;

const message = (e: unknown, fallback: string) => (e instanceof Error ? e.message : fallback);

export default function Dashboard() {
  // Scoring and analysis are committee/admin endpoints; interviewers get their
  // own pre-brief view later (COM-03).
  const { ready } = useAuth({ requireAuth: true, roles: ["committee", "admin"] });

  const [scorer, setScorer] = useState<Scorer>("baseline");
  const [rawRanked, setRawRanked] = useState<RankedCandidate[]>([]);
  const [knownTotal, setKnownTotal] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [aiDetections, setAiDetections] = useState<Record<string, AIDetectionResult>>({});
  const [feynmanScores, setFeynmanScores] = useState<Record<string, FeynmanScore>>({});
  const [videoAnalyses, setVideoAnalyses] = useState<Record<string, VideoAnalysis>>({});
  const [ledgers, setLedgers] = useState<Record<string, CandidateLedger>>({});
  const [ledgerErrors, setLedgerErrors] = useState<Record<string, string>>({});
  const [cohortLedgers, setCohortLedgers] = useState<CandidateLedger[]>([]);
  const [detectLoading, setDetectLoading] = useState(false);

  const [filter, setFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(0);
  const [weights, setWeights] = useState<Record<string, number>>({ ...DEFAULT_WEIGHTS });

  const loadRanking = useCallback(async (which: Scorer) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.scoring.rank(which);
      setRawRanked(data);
      if (which === "baseline") setKnownTotal(data.length);
    } catch (e) {
      setRawRanked([]);
      setError(message(e, "Failed to load"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (ready) loadRanking(scorer);
  }, [ready, scorer, loadRanking]);

  useEffect(() => {
    if (!ready) return;
    api.ledger.list().then(setCohortLedgers).catch(() => setCohortLedgers([]));
  }, [ready]);

  const changeScorer = (next: Scorer) => {
    if (next === scorer) return;
    setScorer(next);
    setFilter("all");
    setCurrentPage(0);
  };

  const ranked = useMemo(() => reweight(rawRanked, weights, scorer), [rawRanked, weights, scorer]);
  const selected = ranked.find((r) => r.candidate.id === selectedId);

  // Per-candidate data, fetched once on first selection.
  useEffect(() => {
    if (!selectedId || feynmanScores[selectedId]) return;
    api.feynman
      .score<FeynmanScore>(selectedId)
      .then((data) => {
        if (data) setFeynmanScores((prev) => ({ ...prev, [selectedId]: data }));
      })
      .catch(() => {});
  }, [selectedId, feynmanScores]);

  useEffect(() => {
    if (!selectedId || ledgers[selectedId] || ledgerErrors[selectedId]) return;
    api.ledger
      .get(selectedId)
      .then((l) => setLedgers((prev) => ({ ...prev, [selectedId]: l })))
      .catch((e) => setLedgerErrors((prev) => ({ ...prev, [selectedId]: message(e, "Failed to load ledger") })));
  }, [selectedId, ledgers, ledgerErrors]);

  const handleDetectAI = async () => {
    if (!selectedId) return;
    setDetectLoading(true);
    try {
      const result = await api.analysis.detectAI(selectedId);
      setAiDetections((prev) => ({ ...prev, [selectedId]: result }));
    } catch {
      /* ignore */
    } finally {
      setDetectLoading(false);
    }
  };

  const handleAnalyzeVideo = async () => {
    if (!selectedId) return;
    try {
      const result = await api.analysis.analyzeVideo(selectedId);
      setVideoAnalyses((prev) => ({ ...prev, [selectedId]: result }));
    } catch {
      /* ignore */
    }
  };

  // Filters, search, pagination
  const filteredByCategory =
    filter === "all"
      ? ranked
      : filter === "hidden_gem"
        ? ranked.filter((r) => isHiddenGem(r, scorer))
        : ranked.filter((r) => groupOf(r, scorer) === filter);

  const q = searchQuery.trim().toLowerCase();
  const filtered = q
    ? filteredByCategory.filter((r) => r.candidate.name.toLowerCase().includes(q) || r.candidate.id.toLowerCase().includes(q))
    : filteredByCategory;

  const paginated = filtered.slice(currentPage * ITEMS_PER_PAGE, (currentPage + 1) * ITEMS_PER_PAGE);

  const stats = [
    { key: "all", label: "Total candidates", count: ranked.length },
    ...groupsFor(scorer).map(({ key, label }) => ({
      key,
      label,
      count: ranked.filter((r) => groupOf(r, scorer) === key).length,
    })),
    ...(scorer === "ai"
      ? [{ key: "hidden_gem", label: "Hidden Gems", count: ranked.filter((r) => isHiddenGem(r, scorer)).length }]
      : []),
  ];

  const rows: RankedCandidate[][] = [];
  for (let i = 0; i < paginated.length; i += 3) rows.push(paginated.slice(i, i + 3));

  return (
    <main className="min-h-screen bg-white">
      <ScrollProgress />
      <DashboardNav />
      <DashboardHeader stats={stats} active={filter} onSelect={setFilter} />

      <div style={{ maxWidth: "1400px", margin: "0 auto", padding: "16px 40px 0" }}>
        <WeightSimulator
          weights={weights}
          onChange={(key, value) => setWeights((prev) => ({ ...prev, [key]: value }))}
          onReset={() => setWeights({ ...DEFAULT_WEIGHTS })}
        />
        <FairnessAudit ranked={ranked} scorer={scorer} ledgers={cohortLedgers} />

        {error && (
          <div className="mb-5 p-4 bg-red-500/10 text-red-400 rounded-2xl text-base border border-red-500/20">{error}</div>
        )}

        {loading && <div className="text-center py-14 text-gray-400 text-lg">Loading candidates...</div>}

        <Toolbar
          scorer={scorer}
          onScorerChange={changeScorer}
          searchQuery={searchQuery}
          onSearch={(v) => {
            setSearchQuery(v);
            setCurrentPage(0);
          }}
          page={currentPage}
          pageSize={ITEMS_PER_PAGE}
          total={filtered.length}
          onPage={setCurrentPage}
        />

        {scorer === "ai" && !loading && !error && (
          <AiCoverageNote scored={rawRanked.length} total={knownTotal} />
        )}

        {!loading && (
          <div className="flex flex-col">
            {rows.map((row, rowIdx) => (
              <div
                key={rowIdx}
                className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 py-5 ${rowIdx < rows.length - 1 ? "border-b-2 border-[#d7d7d7]" : ""}`}
              >
                {row.map((r) => (
                  <CandidateCard key={r.candidate.id} ranked={r} scorer={scorer} onSelect={() => setSelectedId(r.candidate.id)} />
                ))}
              </div>
            ))}
          </div>
        )}

        {filtered.length === 0 && !loading && ranked.length > 0 && (
          <div className="text-center py-14 text-gray-400 text-lg">No candidates match this filter.</div>
        )}
      </div>

      {selected && (
        <CandidateDetail
          key={selected.candidate.id}
          candidate={selected.candidate}
          scorer={scorer}
          score={scoreOf(selected)}
          ledger={ledgers[selected.candidate.id]}
          ledgerError={ledgerErrors[selected.candidate.id] ?? null}
          aiDetection={aiDetections[selected.candidate.id] || null}
          feynmanScore={feynmanScores[selected.candidate.id] || null}
          videoAnalysis={videoAnalyses[selected.candidate.id] || null}
          detectLoading={detectLoading}
          onClose={() => setSelectedId(null)}
          onDetectAI={handleDetectAI}
          onAnalyzeVideo={handleAnalyzeVideo}
        />
      )}

      <DashboardFooter />
    </main>
  );
}

/** `rank?scorer=ai` lists only applicants with a stored successful run (FND-04 PR 3). */
function AiCoverageNote({ scored, total }: { scored: number; total: number | null }) {
  const of = total !== null ? ` of ${total}` : "";
  if (scored === 0) {
    return (
      <div className="text-center py-14 px-6 rounded-2xl border-2 border-dashed border-[#d7d7d7] mb-4">
        <p className="text-lg font-semibold text-[#141414]">No candidate has a stored AI score yet</p>
        <p className="text-sm text-[#969696] mt-1">
          Only successful scoring runs are ranked. Candidates without one are left out rather than shown as zero.
        </p>
      </div>
    );
  }
  return (
    <p className="mb-2 text-sm text-[#5d5d5d]">
      AI score stored for {scored}
      {of} candidates. The rest have no successful run yet and are not ranked; that is not a low score.
    </p>
  );
}
