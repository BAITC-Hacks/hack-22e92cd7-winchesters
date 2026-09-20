# Production Readiness — Async Vision, Cost, Deployment, Security

> This file is the bridge from "polished MVP" to "self-sustainable pilot" and
> keeps doors open toward production. Nothing here blocks the hackathon;
> several items (cost guardrails, model routing) directly help it.

---

## Async vision

_Agreed: sync SQLAlchemy now → clear path later._

**Stage 1 — hackathon/pilot (what Phases D+F deliver):**
- DB: synchronous SQLAlchemy 2.0. DB-only endpoints are `def` (FastAPI
  threadpools them — sync is safe). AI endpoints are `async def` with
  `AsyncAnthropic`; any DB access inside them goes through
  `await run_in_threadpool(...)`.
- This is correct and fast enough for hundreds of candidates and tens of
  concurrent users. Don't complicate it earlier than needed.

**Stage 2 — pilot under load (config, not rewrites):**
- Run `uvicorn` with multiple workers (`--workers 4`) — safe **only after
  Phase D** removed all in-process state (this is *the* hidden reason D matters:
  today, two workers would each have their own `_score_cache` and disagree).
- Tune the SQLAlchemy pool (`pool_size`, `max_overflow`) and the anyio
  threadpool if `run_in_threadpool` saturates.
- Move Feynman *live* session reads/writes to Redis **only if** measured DB
  chatter on `/chat` becomes a bottleneck (it won't at pilot scale).

**Stage 3 — production (the actual async migration, mechanical):**
1. Swap driver: `postgresql+psycopg://` → keep psycopg3 (it has native async) —
   `create_async_engine(settings.database_url)`.
2. `sessionmaker` → `async_sessionmaker`; `get_db` becomes an async generator
   yielding `AsyncSession`.
3. Each endpoint: `def` → `async def`; `session.execute(...)` →
   `await session.execute(...)`; `commit`/`refresh` get `await`.
4. Delete the `run_in_threadpool` wrappers in AI endpoints (sessions are now
   native async).
5. Migrate router-by-router; sync and async engines can coexist during the
   transition (two engines, one DB).
- **Trigger to actually do this:** sustained concurrency where threadpool size
  (≈40) becomes the ceiling — i.e., hundreds of simultaneous users. Not before.

**Background jobs ladder:** F3's in-process jobs table → `arq` (Redis-based,
asyncio-native, tiny) when jobs must survive restarts → a dedicated worker
service when scale demands it. That last step is the natural first **Go
service** if the team wants one: a queue consumer is Go's sweet spot and is
cleanly separable behind the jobs table contract. Decision deferred until F3
measurably hurts.

**Streaming ladder:** AL6's SSE for chat → consider WebSockets only if
bidirectional needs appear (they haven't).

---

## Cost self-sustainability

_Broke-students → pilot budget._

Current pricing (verify at platform.claude.com/docs/en/pricing before big
decisions): Opus 4.8 $5/$25 per MTok · Sonnet 5 $3/$15 (intro $2/$10 through
2026-08-31) · Haiku 4.5 $1/$5. Batches API = 50% off everything. Cache reads
≈ 0.1× input price.

**1. Model routing (A2's two settings; extend as needed):**

| Task | Traffic shape | Route | Rationale |
|---|---|---|---|
| Arman chat persona | many small calls, latency-sensitive (voice) | `claude-haiku-4-5` (A/B first) | persona ≠ judgment; 3–5× cheaper; fastest |
| Feynman evaluation, AI scoring, detection qualitative, growth letters | few, quality-critical | `claude-sonnet-5` default; `claude-opus-4-8` if eval shows it pays | committee-facing judgment |
| Quiz answering (Arman answering as student) | small | follows chat model | same persona |

**2. Prompt caching:** multi-turn Feynman chat — breakpoint on the last message
block each turn (spec in feature-arman-live.md). Verify with
`usage.cache_read_input_tokens`; below the model's minimum cacheable prefix it
silently no-ops — measure, don't assume.

**3. Message Batches API (50% off) for anything overnight:** batch-scoring a
cohort, regenerating growth letters, essay-similarity re-runs after data
changes. Shape: submit all candidates as batch requests keyed by
`custom_id=candidate_id`, poll until `ended`, upsert results (order is not
guaranteed — always match by `custom_id`). Fits perfectly with "pre-score the
night before the demo."

**4. Budget guardrails (must-have before any public URL):**
- A `usage_log` table: per call — endpoint, model, input/output/cache tokens
  (from `response.usage`), timestamp. `llm.py` is the natural place: both
  `complete_json` and `complete_chat` already log model, in/out tokens and stop
  reason, so this is swapping that `logger.info` for a row write — every call in
  the product goes through those two functions. A `GET /api/admin/usage` sums by day.
- Daily budget env var; when exceeded, guest/sandbox endpoints return a
  friendly 503 (`DEMO_KILL_SWITCH` machinery, wired in AL3/Fool-the-Machine).
- Per-IP rate limits (slowapi) on every unauthenticated endpoint.

**5. Free-tier infra map (pilot at ~$0/month):**

| Piece | Option | Notes |
|---|---|---|
| Postgres | Neon / Supabase free tier | ~0.5 GB is plenty for a cohort |
| Backend | Fly.io / Railway / Render hobby tier | one small container; watch sleep-on-idle for demos |
| Frontend | Vercel free | Next.js native; set `NEXT_PUBLIC_API_URL` |
| Whisper sidecar | same host as backend (Fly machine) or on-demand | CPU-only, batch use |
| Uptime | UptimeRobot free | pings /healthz |
| Errors | Sentry free tier | FastAPI + Next.js SDKs |

---

## Operability checklist (pilot bar)

- **Health endpoints:** `GET /healthz` (process up) and `GET /readyz` (DB
  reachable; whisper optional). Wire into compose healthchecks + UptimeRobot.
- **Structured logging:** `structlog` JSON logs; middleware injects a request
  id; log every AI call's model + token usage + latency (feeds the usage table).
- **Error tracking:** Sentry SDK in both apps; release tags from git SHA.
- **Metrics (later):** `prometheus-fastapi-instrumentator` when there's
  somewhere to look at them; not before.
- **Backups:** managed Postgres tiers include snapshots; additionally a nightly
  `pg_dump` artifact in CI for belt-and-braces. **Test one restore.**
- **Migrations discipline:** every schema change via Alembic; CI runs
  `alembic upgrade head` against a scratch DB to catch broken migrations.

## LLM quality ops (what makes prompt work safe)

- **Prompts as versioned constants:** each prompt lives in code (or
  `backend/prompts/`) with a `PROMPT_VERSION`; log the version with every call
  so score drift is attributable.
- **Golden set:** the 16 synthetic candidates with expected score *ranges*
  (not exact values) per dimension; a `pytest -m golden` suite that runs against
  the real API on demand (costs cents) before any prompt/model change ships.
  This is the graduation of `notebooks/validation_analysis.py` into CI-adjacent
  tooling.
- **Structured outputs everywhere** (A3b) so schema errors are impossible, and
  parser fixtures (B1) so format changes are caught in unit tests.

## Security & compliance (pilot bar — this is real-people data, minors)

- Secrets only via env/secret store (A2 removed the last hardcoded secret in E2).
- HTTPS everywhere (platform-provided TLS); HSTS at the proxy.
- AuthN/Z: Phase E; add token refresh or short-lived tokens + re-login for
  pilot; consider httpOnly cookie sessions when the frontend moves same-origin.
- **PII scope grows at pilot:** real applications need a data-protection story —
  Kazakhstan's personal-data law applies, and applicants are minors: collect
  minimal data, document retention (e.g., delete cohort N months after
  decisions), parental/consent language in the application flow, and a
  written answer to "what leaves the machine?" (only anonymized text to
  Anthropic — the existing `privacy.py` design, extended: mask names inside
  essay *text*, not just the name field — current regexes cover emails/phones
  only; add a pass that masks the applicant's own name occurrences).
- Input hardening: essay/transcript length caps at the API boundary (pydantic
  validators), upload size/type caps (LM1), rate limits (slowapi) on all
  public endpoints.
- Dependency hygiene: `pip-audit` step in CI.

## Multi-tenancy (production door — design note only)

When a second university appears: add `org_id` to `users`, `candidates`, and
all result tables; scope every query by the requester's org; per-org rubric
weights and topics become rows instead of constants. The D2 schema deliberately
avoids anything that would make this retrofit painful (no cross-candidate
global uniqueness except IDs). Do **not** build it before customer #2 exists.
