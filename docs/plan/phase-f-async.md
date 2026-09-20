# Phase F — Async Correctness & Performance

> Highest value-per-hour in the whole plan, and a **hard prerequisite for Arman
> Live judge mode** (many concurrent chat sessions). Independent of D/E — do it
> right after Phase A.
> Prerequisite reading: the asyncio row of the Go-dev primer in
> [../backend-plan.md](../backend-plan.md).

**The bug, precisely:** `compute_ai_score`, `detect_ai_content`, and
`analyze_video` are `async def` functions that call the **synchronous**
`client.messages.create(...)`. Python's event loop is one thread with
cooperative scheduling; a blocking call inside `async def` doesn't just slow
that request — it freezes *every* request on the server until Claude responds
(seconds). The Feynman endpoints are plain `def` (threadpooled), so they don't
freeze the loop, but they still burn one threadpool worker per in-flight call.

---

## F1 — AsyncAnthropic in the async paths · S

**Files:** `backend/ai_client.py` (A3 already exposes `get_async_client()`),
`backend/scoring/ai_scorer.py`, `backend/scoring/ai_detector.py`,
`backend/scoring/video_analyzer.py`.

**Spec:**
- In each of the three async functions, take the client from
  `get_async_client()` and `await client.messages.create(...)`. Everything else
  in those functions (prompt building, parsing) is CPU-trivial and stays as-is.
- Keep SDK defaults for retries (2, with backoff on 429/5xx) — do **not**
  hand-roll retry loops. Set an explicit per-call `timeout` (e.g.
  `client.with_options(timeout=60.0)`) so a hung request can't pin a coroutine
  forever.
- Once D lands, DB reads/writes inside these async endpoints wrap the sync
  session call: `await run_in_threadpool(save_score, db, score)`
  (`fastapi.concurrency.run_in_threadpool`) — a sync DB call directly in
  `async def` would re-introduce the freeze, just shorter.

**Convert Feynman deliberately in the same PR:** `feynman.py`'s start/chat/
finish become `async def` + `await` on the async client. Rationale: judge mode
needs N concurrent chats; on the event loop they cost ~nothing while awaiting,
versus one threadpool worker each (default pool ≈ 40) as sync `def`.

**Done when (the proof matters):** start an AI scoring call, then immediately
`GET /api/candidates/` from a second terminal — the second request returns
instantly instead of queuing behind the first. Write this as a test:
`asyncio.gather` a mocked slow AI call (mock sleeps 1s via `asyncio.sleep`) and
a candidates request; assert the candidates request completes first.

**Gotchas:** never mix — `await` only inside `async def`; a `def` endpoint
can't await. Grep for any remaining `get_client()` (sync) users after this PR;
the sync client should have zero call sites left (delete it, or keep it only
for the seed/CLI scripts).

---

## F2 — Parallel batch scoring · S

**Why:** `/api/scoring/ai/all` loops candidates one at a time — 16 candidates
× ~5s = ~80s wall-clock and a guaranteed HTTP timeout behind any proxy. With F1
done, run them concurrently with a cap.

**New concepts:** `asyncio.gather(*tasks)` ≈ launching goroutines + WaitGroup;
`asyncio.Semaphore(n)` ≈ a buffered channel used as a concurrency limiter.

**Spec (in `scoring.py`):**
- Wrap `compute_ai_score(c)` in `async def _bounded(c)` that acquires a
  `Semaphore(4)` (tune to the org's Anthropic rate-limit tier; 4 is safe to start).
- `results = await asyncio.gather(*[_bounded(c) for c in candidates], return_exceptions=True)`.
- Keep the existing per-candidate failure behavior: an exception becomes the
  "Scoring failed" placeholder score, and one failure must not sink the batch
  (`return_exceptions=True` does exactly this).
- Persist results (post-D) with `run_in_threadpool`.

**Done when:** scoring 16 candidates takes ~⌈16/4⌉ × single-call time instead of
16×; a mocked 429 on one candidate yields 15 real scores + 1 failure record.

**Gotchas:** the semaphore must be created inside the running loop (module-level
creation is fine on Python 3.12 but create-per-request is simplest); watch
Anthropic 429s in logs and lower the cap if they appear — the SDK retries them,
but retries burn latency.

---

## F3 — Background jobs (stretch; pre-req for very large cohorts) · M

**Why:** even parallel, "score all" for a 500-candidate real cohort is minutes —
too long for one HTTP request. Fire-and-poll instead.

**Spec (minimal version, no new infra):**
- `POST /api/scoring/ai/all` creates a row in a new `jobs` table
  (`id, kind, status queued|running|done|failed, progress int, total int,
  error, created_at`) and schedules the work with FastAPI's `BackgroundTasks`
  (or `asyncio.create_task` guarded against server shutdown). Returns `202 {job_id}`.
- Worker updates `progress` per candidate; `GET /api/jobs/{id}` returns status.
- Frontend polls and shows a progress bar.

**Production note:** the honest limits of in-process background tasks — they die
with the process and don't scale past one instance. The upgrade path (documented
in [production-readiness.md](production-readiness.md)) is a real queue; that is
also the natural first **Go service** if the team ever wants one: a small worker
consuming a jobs table/queue and calling the scoring API. Don't build that until
F3's limits actually hurt.

**Done when:** kicking off "score all" returns immediately; progress reaches
`total`; killing the request/browser doesn't kill the job; a second "score all"
while one runs either queues or 409s (pick one, document it).

---

## Also in this phase: streaming (feeds Arman Live)

`client.messages.stream(...)` (async) yields text deltas as they generate. Not
required for F1/F2 correctness, but Arman Live's voice mode wants
time-to-first-word, and the SSE endpoint spec lives in
[feature-arman-live.md](feature-arman-live.md#al6--streaming-replies-stretch).
Keep F1's code shaped so the chat call site can switch from
`await client.messages.create` to `client.messages.stream` without touching the
rest (i.e., isolate the "call Claude, get text" step in one helper).
