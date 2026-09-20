# Phase D — Persistence (Postgres + SQLAlchemy 2.0 + Alembic)

> The big structural change. Replaces the racy `candidates.json` writes and
> **every** module-level cache dict: `_score_cache`/`_baseline_cache`
> (scoring.py), `_detection_cache`/`_video_cache` (analysis.py),
> `_sessions`/`_score_cache` (feynman.py), `_users` (auth.py),
> `_candidates_cache` (candidates.py).
> Prerequisites: A2 (DATABASE_URL in settings), C1 (Postgres running), B1 (tests).
> Decision (agreed): **synchronous SQLAlchemy 2.0** now; the async migration
> vision lives in [production-readiness.md](production-readiness.md#async-vision).

Why sync is fine here: FastAPI runs `def` endpoints in a threadpool, so sync DB
calls don't block the event loop. The few endpoints that mix AI (async) + DB get
`run_in_threadpool` around the DB call (spec in Phase F). Async SQLAlchemy adds
real complexity (async engine, greenlet internals, different session rules) for
no benefit at this scale.

---

## D1 — Spike: learn the ORM on a throwaway script · M

**Why:** don't learn SQLAlchemy inside a 15-file PR.

**Steps:** in the scratch area (not committed), write a 30-line script:
define one mapped class (`class Note(Base): __tablename__=...; id: Mapped[int] =
mapped_column(primary_key=True); text: Mapped[str]`), `Base.metadata.create_all(engine)`,
insert via `Session(engine)` + `session.add` + `commit`, query via
`session.execute(select(Note).where(...)).scalars().all()`.

**Done when:** you can explain, in Go terms: engine ≈ `*sql.DB` (pool),
Session ≈ a per-request unit-of-work/transaction wrapper, mapped class ≈ struct
with ORM tags, `select()` ≈ query builder. And: **2.0 style only** — if a
tutorial shows `session.query(...)`, it's the legacy 1.x API; skip it.

---

## D2 — Schema design · M

**Pragmatic rule:** promote to real columns only what we filter/join on; keep
deeply nested application data as **JSONB** (Postgres' binary JSON — queryable
if ever needed, flexible now). Don't over-normalize a 5-week-old data model.

**Tables:**

| Table | Columns (→ = FK) | Replaces |
|---|---|---|
| `users` | `id` (pk, text `u-…`), `email` (unique, indexed), `password_hash`, `full_name`, `role` (default `applicant`), `candidate_id` (nullable → candidates), `created_at` | `_users` dict |
| `candidates` | `id` (pk, text `c-###`), `name`, `age`, `application` JSONB, `essay` JSONB, `interview_transcript` text, `recommendation_summary` text, `video_link`, `video_transcript`, `created_at` | `candidates.json` |
| `scores` | `id` serial pk, `candidate_id` → candidates (indexed), `scorer_type` (`baseline`\|`ai`), `overall_score` float, `recommendation`, `summary`, `dimensions` JSONB, `weights` JSONB (what weights produced it), `created_at`; **unique (candidate_id, scorer_type)** — upsert semantics | `_score_cache`, `_baseline_cache` |
| `detections` | `candidate_id` pk → candidates, `authenticity_score`, `flags` JSONB, `explanation`, `stylometry` JSONB, `created_at` | `_detection_cache` |
| `video_analyses` | `candidate_id` pk → candidates, full `VideoAnalysisResult` fields (JSONB for lists), `is_mock` bool | `_video_cache` |
| `feynman_sessions` | `session_id` pk (text), `candidate_id` (nullable — guest mode!), `guest_name` (nullable), `topic_id`, `system` text, `messages` JSONB, `exchange_count` int, `status` (`active`\|`finished`\|`abandoned`), `created_at`, `updated_at` | `_sessions` |
| `feynman_scores` | `id` serial pk, `candidate_id` (nullable), `guest_name` (nullable), `session_id`, `topic_id`, the six score floats, `summary`, `quiz_answers` JSONB, `understanding_trace` JSONB (Arman Live), `created_at` | feynman `_score_cache` |
| `growth_letters` | `candidate_id` pk, `letter` text, `language`, `status` (`draft`\|`approved`), `created_at` | (new — No Dead Ends) |

Notes:
- `feynman_scores` is append-only (a candidate may retry) — leaderboard takes
  best-per-person.
- ID strategy: keep `c-###` for frontend compatibility; generate inside a
  transaction with `SELECT ... FOR UPDATE` on a counter row **or** simplest:
  a Postgres sequence rendered as `c-{seq:03d}`. Either kills the race that
  bit the team before.
- Draw the ERD (even in ASCII in this file's PR) and get Rauan's ack before D3.

---

## D3 — Engine, session dependency, Alembic init · S

**Files:** new `backend/db/__init__.py`, `backend/db/session.py`,
`backend/db/models.py`; new `alembic/` + `alembic.ini` at repo root; add
`sqlalchemy>=2.0`, `alembic`, `psycopg[binary]` to requirements.

**Spec — `session.py`:**
- `engine = create_engine(settings.database_url, pool_pre_ping=True)`.
- `SessionLocal = sessionmaker(bind=engine)`.
- `def get_db(): db = SessionLocal(); try: yield db; finally: db.close()` — the
  FastAPI dependency every endpoint takes as `db: Session = Depends(get_db)`.

**Alembic steps:**
1. `alembic init alembic`; in `alembic/env.py` set
   `target_metadata = Base.metadata` **and import `backend.db.models`** (the
   classic trap: autogenerate sees only imported models) and read the URL from
   `settings.database_url`, not alembic.ini.
2. `alembic revision --autogenerate -m "initial schema"` → **read the generated
   file** (autogenerate is a draft, not gospel).
3. `alembic upgrade head` → verify tables in Adminer.

**Done when:** fresh DB + `alembic upgrade head` creates all D2 tables; a second
`upgrade head` is a no-op.

---

## D4 — Migrate the candidates router · M

**Why first:** smallest router, and it kills the two worst bugs — the mutated
global list cache and the whole-file JSON rewrite on every create (data loss on
concurrent writes).

**Spec (endpoint by endpoint):**
- `GET /api/candidates/` → `select(CandidateRow)`, map rows → existing
  `Candidate` pydantic model (response shape unchanged — frontend untouched).
- `GET /{id}` → `session.get(CandidateRow, id)` or 404.
- `POST /` → insert inside one transaction with the sequence-based ID; return
  the created candidate.
- Delete `_load_candidates`, `_save_candidates`, `_candidates_cache`. Keep a
  thin `get_candidate_or_404(db, id)` helper for other routers (replaces the
  `_get_candidate` import they currently share).
- Write a mapping layer (`row_to_model` / `model_to_row`) in one place —
  `application`/`essay` go through `model_dump()`/`model_validate()` to/from JSONB.

**Done when:** all candidate endpoints work against Postgres; two parallel
create requests (test with `httpx` + threads) produce two distinct IDs;
`candidates.json` is no longer written at runtime (it becomes the seed fixture).

---

## D5 — Migrate scores, detections, video, Feynman, users · M/L

Split into 2–3 PRs (scoring; analysis; feynman+auth-store) if review size balloons.

**Spec:**
- **scoring.py:** `_score_cache`/`_baseline_cache` → `scores` table with
  **upsert** (`INSERT ... ON CONFLICT (candidate_id, scorer_type) DO UPDATE`).
  Preserve current behaviors exactly: rank auto-computes baseline when missing;
  `compare` 404s when AI score absent; `override` mutates the stored dimensions
  JSON and recomputes overall. Store the weights used alongside.
- **analysis.py:** cache-hit check becomes a SELECT; result INSERT on first
  computation. Same response models.
- **feynman.py:** sessions move to `feynman_sessions` — every `/chat` turn
  appends to the `messages` JSONB and bumps `exchange_count` in one UPDATE.
  **Message order must round-trip exactly** (JSONB preserves array order — the
  risk is code that rebuilds dicts, not the DB). `/finish` marks
  `status='finished'` and inserts into `feynman_scores` (keep the row; don't
  delete sessions — they're audit data + Arman Live's trace source).
- **auth.py:** `_users` → `users` table (Phase E does the security part; this
  PR only moves storage; keep the hashing as-is to decouple the two changes).

**Done when:** restart the server mid-flow — scores, detections, a half-finished
Feynman session, and registered users all survive. `grep -rn "_cache\|_sessions\s*:" backend/routers backend/scoring`
shows no module-level mutable stores left.

---

## D6 — Seed script + test fixtures · S

**Spec:** `backend/db/seed.py` — reads `backend/data/candidates.json`, inserts
candidates **only if the table is empty** (idempotent); seeds the committee
user. Runable as `python -m backend.db.seed`; called in CI before tests and
documented in the README. Tests get a `db` fixture that runs migrations against
a disposable schema (or a dockerized test DB in CI) and truncates between tests.

**Done when:** `docker compose up -d && alembic upgrade head && python -m backend.db.seed`
on a clean machine yields the working app with 16 candidates.
