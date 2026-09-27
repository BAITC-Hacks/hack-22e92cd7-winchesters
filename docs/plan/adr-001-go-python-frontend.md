# ADR-001 — Backend language split (Go alongside Python) and frontend direction

> Status: **proposed** · Date 2026-09-12 · Supersedes the informal 2026-07-02 conclusion
> ("consider Go only if the project productionizes") with a concrete seam and a gate.

---

## Part A — Should Go come into the backend?

### Verdict

**Yes — but exactly one Go service, behind a contract, and not before week 3.**

Do **not** split the current backend. Fix Python in place for weeks 1–2 (persistence, async, auth,
tests, Docker). Then introduce one greenfield Go service. The candidate services, in order of how
well they fit Go:

| Candidate | Fit | Verdict |
|---|---|---|
| **Arman Live realtime hub** — WebSocket/SSE fan-out for 30 judge phones + leaderboard broadcast | Connection-heavy, latency-sensitive, stateless per message, no LLM SDK needed | **Best pick if Arman Live is the killer feature.** Greenfield, so zero rewrite risk. |
| **Batch scoring worker** — durable "score 500 candidates" jobs with progress, retries, rate-limit-aware concurrency | Queue consumer + bounded fan-out is Go's sweet spot | **Best pick if the pilot story matters more** than demo-day participation. Already flagged as "the natural first Go service" in [production-readiness.md](production-readiness.md). |
| **API gateway / BFF** — auth, rate limiting, usage metering, request IDs, org scoping | Clean, and lets auth be built in the language Almas is strongest in | Attractive but **skip for now**: Phase E in FastAPI gets you the same security outcome for a fraction of the moving parts. |
| Candidate/score CRUD | — | **No.** Pydantic + SQLAlchemy already do this. Rewriting buys nothing and pays for the DB layer twice. |

**Pick one.** Not two. A three-person team in one month cannot absorb two new services.

### The contract that makes this safe

The split only works if the boundary is a real interface, not a shared codebase:

- **Go never calls the Anthropic API** and never owns the scoring schema.
- **Python owns judgment**: it exposes an internal endpoint (e.g. `POST /internal/score`) and owns
  the DB schema and migrations for candidates/scores.
- **Go owns connections, queues, timeouts, retries, backpressure, fan-out** — and at most its own
  tables (jobs, live sessions), never the scoring tables.
- The seam is HTTP + a table contract, both versioned. If the Go service dies, the Python app still
  works in degraded mode (that property is what makes the split reversible).

### Why the AI core stays Python

These are the reasons that actually hold, as opposed to "Python is the ML language":

1. **SDK depth.** Structured outputs, streaming, prompt caching, and the Message Batches API are
   first-class in the Python SDK. In Go you would be maintaining the gap yourself — and the Batches
   API alone is a 50% cost cut you do not want to hand-roll.
2. **The local-models plan requires it.** faster-whisper, multilingual-e5 embeddings,
   sentence-transformers — [feature-local-models.md](feature-local-models.md) has no Go path at all.
3. **Iteration velocity beats runtime speed here.** The bottleneck is a 15-second network call, not
   the interpreter. Prompts and parsers change daily; that work belongs in the fastest-to-edit
   language, not the fastest-to-execute one.
4. **Translation risk.** `baseline.py` + `signal_extractor.py` are ~760 LOC of tuned heuristics, and
   their output *is* the product. Porting them is a week of pure translation with a real chance of
   silent scoring drift.

### The honest cost of adding Go

Say this out loud before committing: two toolchains, two Dockerfiles, two CI matrices, a schema to
keep in sync, service-to-service auth, tracing you did not previously need, and a debugging story
that now crosses a process boundary. For three people in a month, that is a real tax.

### The gate

Introduce Go when **either**:
- the component is greenfield (the realtime hub is — this is why it's the safest entry point), **or**
- Python's single service has been *measured* and found wanting at a specific, named thing
  (e.g. threadpool saturation under concurrent judge sessions).

"I want to use Go" is not a gate. Which brings us to:

### If the motivation is ownership rather than architecture

Legitimate — and there is a zero-risk outlet that is still real Go work:

- A **Go CLI for operations**: seed, migrate-check, cohort export, usage/cost report, golden-set runner.
- A **Go load-test harness** for the Arman Live hub (simulate 50 phones teaching at once). You need
  this number for the pitch anyway, and nothing else on the team will produce it.

Both ship value in days, neither can break the product, and both are genuinely idiomatic Go.

---

## Part B — What should the frontend be?

### Verdict

**Stay on Next.js. The framework is already the right one; the way it is used is wrong.**

Current state: Next.js 16 + React 19 + Tailwind v4 on the App Router — but used as four giant
`"use client"` components fetching in `useEffect`. Switching frameworks (Vite SPA, SvelteKit, …)
burns one to two weeks and produces zero user-visible value, against a design that is already
implemented on this stack.

Next.js specifically earns its keep here for three things you actually need:

1. **Route handlers / server-side fetching** — so the browser stops talking directly to FastAPI and
   tokens stop living in `localStorage`.
2. **Streaming + Suspense** — the AI scoring UI is the archetypal use case for progressive rendering
   of slow work.
3. **Vercel free tier** — one-click Next deploys and a preview URL per PR, which is how the designer
   reviews work without a local setup.

### Four changes, in priority order

**1. Same-origin `/api` proxy (highest leverage change on either side of the stack).**
Today `NEXT_PUBLIC_API_URL` is inlined at build time, the browser calls FastAPI cross-origin, CORS is
`*`, and the token sits in `localStorage`. Proxying `/api/*` through Next (rewrite or route handler)
fixes all four at once:
- no CORS configuration at all,
- httpOnly cookie sessions become possible,
- the frontend image stops being welded to one API host (a direct Docker win — see
  [phase-c-docker.md](phase-c-docker.md)),
- FastAPI can live on a private network with no public port.

**2. Split the monoliths and add a data layer.** Server Components for shell and static content,
small client components for interactive islands, and TanStack Query (or SWR) for fetching — caching,
retries, polling (needed once scoring becomes a job), and request dedup, instead of 23 hand-rolled
`useState`/`useEffect` pairs in one 1,388-line file.

**3. Generate API types from the OpenAPI schema.** FastAPI already publishes it; `lib/types.ts` is
hand-maintained and *will* drift from the Pydantic models. One CI step (`openapi-typescript`) turns a
hoped-for contract into an enforced one. This is a whole class of production bug deleted.

**4. For Arman Live:** voice needs `MediaRecorder` / Web Speech API in a client component plus SSE
for the understanding meter. Next handles this fine — but budget mobile-Safari testing time, because
Web Speech support is uneven. Plan the `MediaRecorder` → Whisper fallback path, which is conveniently
the same local-whisper sidecar you already want.

### Explicitly not doing

- **No state-management library** (Redux/Zustand). Server state via Query + UI state in the URL is enough.
- **No component-library swap.** Tailwind + the existing design is fine; restyling is not progress.
- **No i18n framework yet** — but *do* extract user-facing strings now (~2 hours). The product is
  Kazakhstan-facing and the AI already replies in three languages; a hardcoded English UI in front of
  a trilingual backend is the kind of thing a sponsor notices immediately.

---

## Resulting target architecture (end of month)

```
Browser ──► Next.js (Vercel / container)
              │  /api/* same-origin proxy
              ▼
         FastAPI  ── Anthropic (judgment, persona)
              │    ── faster-whisper sidecar (optional profile)
              ▼
         Postgres  ◄── one Go service (realtime hub OR batch worker), own tables only
```

One database, one judgment service, one optional Go service with a narrow contract. Reversible at
every step.
