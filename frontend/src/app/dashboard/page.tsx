"use client";

// The admissions dashboard: loads data, holds selection and filter state, lays
// out the views. Rendering lives in src/components/.

import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { DEFAULT_WEIGHTS, groupOf, groupsFor, isHiddenGem, reweight, scoreOf, type Scorer } from "@/lib/dashboard";
import type { AIDetectionResult, CandidateLedger, CounterfactualProbeResult, FeynmanScore, InterviewerPreBrief, RankedCandidate, VideoAnalysis } from "@/lib/types";
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
  const [counterfactualProbes, setCounterfactualProbes] = useState<Record<string, CounterfactualProbeResult>>({});
  const [probeLoading, setProbeLoading] = useState(false);
  const [probeError, setProbeError] = useState<string | null>(null);
  const [preBriefs, setPreBriefs] = useState<Record<string, InterviewerPreBrief>>({});
  // Every stored snapshot, loaded once. A candidate absent from it has no
  // ledger: that is known without asking for a 404 (LED-12).
  const [cohortLedgers, setCohortLedgers] = useState<CandidateLedger[] | null>(null);
  const [ledgerListError, setLedgerListError] = useState<string | null>(null);
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
    api.ledger
      .list()
      .then(setCohortLedgers)
      .catch((e) => {
        setCohortLedgers([]);
        setLedgerListError(message(e, "Failed to load ledgers"));
      });
  }, [ready]);

  const changeScorer = (next: Scorer) => {
    if (next === scorer) return;
    setScorer(next);
    setFilter("all");
    setCurrentPage(0);
  };

  const ranked = useMemo(() => reweight(rawRanked, weights, scorer), [rawRanked, weights, scorer]);
  const selected = ranked.find((r) => r.candidate.id === selectedId);
  const ledgerOf = (id: string) => cohortLedgers?.find((l) => l.applicant_ref === id);
  const selectedLedger = selectedId ? ledgerOf(selectedId) : undefined;

  // Per-candidate data, fetched once on first selection.
  useEffect(() => {
    if (!selectedId || feynmanScores[selectedId]) return;
    api.feynman
      .score(selectedId)
      .then((data) => {
        if (data) setFeynmanScores((prev) => ({ ...prev, [selectedId]: data }));
      })
      .catch(() => {});
  }, [selectedId, feynmanScores]);

  // The pre-brief is a projection of a stored ledger: only asked for when one exists.
  const hasSelectedLedger = Boolean(selectedLedger);
  useEffect(() => {
    if (!selectedId || !hasSelectedLedger || preBriefs[selectedId]) return;
    api.committee
      .preBrief(selectedId)
      .then((brief) => setPreBriefs((prev) => ({ ...prev, [selectedId]: brief })))
      .catch(() => {});
  }, [selectedId, hasSelectedLedger, preBriefs]);

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

  const handleRunProbe = async () => {
    if (!selectedId) return;
    setProbeLoading(true);
    setProbeError(null);
    try {
      const result = await api.fairness.probe(selectedId);
      setCounterfactualProbes((prev) => ({ ...prev, [selectedId]: result }));
    } catch (e) {
      setProbeError(message(e, "Fairness probe unavailable"));
    } finally {
      setProbeLoading(false);
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
        <FairnessAudit ledgers={cohortLedgers ?? []} />

        {error && (
          <div className="mb-5 p-4 bg-red-500/10 text-red-400 rounded-2xl text-base border border-red-500/20">{error}</div>
        )}

        {loading && <div className="text-center py-14 text-ink-3 text-lg">Loading candidates...</div>}

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
                className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 py-5 ${rowIdx < rows.length - 1 ? "border-b-2 border-line" : ""}`}
              >
                {row.map((r) => (
                  <CandidateCard key={r.candidate.id} ranked={r} scorer={scorer} onSelect={() => setSelectedId(r.candidate.id)} />
                ))}
              </div>
            ))}
          </div>
        )}

        {filtered.length === 0 && !loading && ranked.length > 0 && (
          <div className="text-center py-14 text-ink-3 text-lg">No candidates match this filter.</div>
        )}
      </div>

      {selected && (
        <CandidateDetail
          key={selected.candidate.id}
          candidate={selected.candidate}
          scorer={scorer}
          score={scoreOf(selected)}
          ledger={selectedLedger}
          preBrief={preBriefs[selected.candidate.id]}
          ledgerError={ledgerListError}
          ledgerMissing={cohortLedgers !== null && !ledgerListError && !selectedLedger}
          aiDetection={aiDetections[selected.candidate.id] || null}
          feynmanScore={feynmanScores[selected.candidate.id] || null}
          videoAnalysis={videoAnalyses[selected.candidate.id] || null}
          counterfactualProbe={counterfactualProbes[selected.candidate.id] || null}
          probeLoading={probeLoading}
          probeError={probeError}
          detectLoading={detectLoading}
          onClose={() => setSelectedId(null)}
          onDetectAI={handleDetectAI}
          onAnalyzeVideo={handleAnalyzeVideo}
          onRunProbe={handleRunProbe}
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
      <div className="text-center py-14 px-6 rounded-2xl border-2 border-dashed border-line mb-4">
        <p className="text-lg font-semibold text-ink">No candidate has a stored AI score yet</p>
        <p className="text-sm text-ink-3 mt-1">
          Only successful scoring runs are ranked. Candidates without one are left out rather than shown as zero.
        </p>
      </div>
    );
  }
  return (
    <p className="mb-2 text-sm text-ink-2">
      AI score stored for {scored}
      {of} candidates. The rest have no successful run yet and are not ranked; that is not a low score.
    </p>
  );
}
