# Phase F — Async Correctness & Performance

> Highest value-per-hour in the whole plan, and a **hard prerequisite for Arman
> Live judge mode** (many concurrent chat sessions). Independent of D/E — do it
> right after Phase A.
>
> **Status 2026-09-20: F1 and F2 are done**, delivered by `backend/llm.py` as part of the
> FND-01/02 work rather than as their own PR. F3 (background jobs) is untouched and is now the
> whole of this phase. Read the two sections anyway — the *done-when* proofs were never run, and
> the streaming note at the bottom still shapes Arman Live.
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

## F1 — AsyncAnthropic in the async paths · **done**

**Shipped as:** `backend/llm.py` constructs one module-level `AsyncAnthropic` with
`max_retries=LLM_MAX_RETRIES` and `timeout=LLM_TIMEOUT_SECONDS` from `settings.py`, and every
call site awaits `llm.complete_json` / `llm.complete_chat`. `ai_scorer.py`, `ai_detector.py` and
`video_analyzer.py` no longer touch a client, and `feynman.py`'s start/chat/finish became
`async def` in the same change — which is what judge mode needs, since N concurrent chats cost
~nothing on the event loop versus one threadpool worker each.

**Still to honor when D lands:** DB reads/writes inside these async endpoints must wrap the sync
session call — `await run_in_threadpool(save_score, db, score)`
(`fastapi.concurrency.run_in_threadpool`). A sync DB call directly in `async def` re-introduces
the freeze, just shorter.

**Done when — and this was never actually proved, so do it:** start an AI scoring call, then
immediately `GET /api/candidates/` from a second terminal; the second request should return
instantly instead of queuing behind the first. Write it as a test: `asyncio.gather` a stubbed
slow `llm.complete_json` (sleeps 1s via `asyncio.sleep`) and a candidates request, assert the
candidates request finishes first. That test does not exist yet — it belongs in Phase B's gap
list.

**Gotchas:** never mix — `await` only inside `async def`; a `def` endpoint can't await. There is
no sync client left anywhere; keep it that way.

---

## F2 — Parallel batch scoring · **done**

**Why:** `/api/scoring/ai/all` looped candidates one at a time — 16 candidates
× ~5s = ~80s wall-clock and a guaranteed HTTP timeout behind any proxy.

**New concepts:** `asyncio.gather(*tasks)` ≈ launching goroutines + WaitGroup;
`asyncio.Semaphore(n)` ≈ a buffered channel used as a concurrency limiter.

**Shipped as:** `routers/scoring.py` does
`asyncio.gather(*(compute_ai_score(c, weights) for c in candidates), return_exceptions=True)`.
The concurrency cap lives one level down, in `llm._limiter` — a single
`asyncio.Semaphore(MAX_CONCURRENT_LLM_CALLS)` (default 4) shared by *every* call path, so
detection and video analysis count against the same budget as scoring rather than each router
enforcing its own.

**One deliberate behavior change from the spec above.** The plan said to keep the "Scoring
failed" placeholder score. The implementation **drops** the failed candidate instead, and logs
it. The reason is worth remembering: the placeholder had `overall_score=0`, which sorts to the
bottom of the ranking — so an API timeout was indistinguishable from a weak application, on the
committee's screen. Silence is the safer failure here. The cost is that the caller cannot tell
16-scored-fine from 12-scored-and-4-timed-out; when Phase D lands, that belongs in a run record,
not a fake score.

**Done when — not yet proved:** scoring 16 candidates takes ~⌈16/4⌉ × single-call time instead
of 16×; a mocked 429 on one candidate yields 15 scores and one logged failure.

**Gotchas:** watch Anthropic 429s in logs and lower `MAX_CONCURRENT_LLM_CALLS` if they appear —
the SDK retries them, but retries burn latency. The semaphore is created at import time, which is
fine on Python 3.12+; if the module is ever imported before the loop exists, this is the first
thing to check.

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
[feature-arman-live.md](feature-arman-live.md#al6--streaming-replies).
That helper now exists: `llm.complete_chat` is the single "call Claude, get text" step, so the
switch to `client.messages.stream` is one function body and no call-site changes. Note that
`complete_chat` passes `thinking={"type": "disabled"}` — see
[phase-a-foundations.md](phase-a-foundations.md#a3--the-single-claude-call-path--done) for why,
and keep it when adding streaming.
