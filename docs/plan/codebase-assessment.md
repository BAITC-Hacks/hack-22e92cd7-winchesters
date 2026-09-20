# Codebase Assessment — 2026-09-12

> Snapshot: branch `feat/docker-compose` at `b401013` plus the uncommitted working tree.
> Scope: ~3,300 LOC Python backend, ~4,100 LOC TypeScript frontend (4 page files), 16 synthetic candidates.

## Headline

**This is a prototype with production-shaped ideas and demo-shaped plumbing.**

The ideas are genuinely pilot-grade: two-stage scoring (deterministic extraction → LLM judgment),
a rule-based baseline kept alive next to the AI scorer, code-computed stylometry, a trajectory
delta instead of a snapshot, a PII layer that exists before anyone asked for it. Those are the
things a university actually buys.

The plumbing is not: nothing survives a restart, one AI call freezes the whole server, auth is
decorative, there are zero tests. The one-month job is to **lift the plumbing to match the ideas —
not to add more ideas.**

---

## What is genuinely good (protect this)

| Asset | Where | Why it matters |
|---|---|---|
| **Two-stage scoring pipeline** | `signal_extractor.py` → `ai_scorer.py` | Facts extracted in pure code; the LLM scores only subjective dimensions. This *is* the auditability story. Do not let it collapse back into one prompt. |
| **Baseline scorer kept alive** | `scoring/baseline.py` (410 LOC) | Produces the pitch's "baseline misses X of our top 10" number, and is a working fallback when the API is down. Most teams delete this. |
| **Code-computed stylometry** | `ai_detector.py` — TTR, hapax ratio, sentence-length variance, essay↔interview vocab overlap | Cheap, reproducible, defensible under Q&A. Language-aware (`detect_language` + per-language filler phrases), which is correct for a KZ/RU/EN product. |
| **Domain model carries provenance** | `models.py` — `DimensionScore` has `confidence`, `evidence_quotes`, `positive_factors`, `concerns` | Designed a step ahead: exactly the primitives Uncertainty Triage and the explainability UI need. |
| **Privacy layer exists at all** | `privacy.py`, called from all three AI modules | Anonymize-before-send was a deliberate design choice, not an afterthought. |
| **Central AI client** | `ai_client.py` (uncommitted) | Phase A3 is effectively done in the working tree; `text_of()` correctly skips thinking blocks. |
| **Real design, implemented** | `frontend/src/app/*` | Weight sliders, committee overrides, baseline-vs-AI comparison, Figma-matched. The UI is ahead of the backend. |

---

## Structural weaknesses, ranked by what they cost the product

### 1. No persistence — the blocking issue, not a nice-to-have

Module-global dicts hold everything:

| State | Location |
|---|---|
| candidates (mutated cache over a JSON file) | `routers/candidates.py:18` |
| AI scores, baseline scores | `routers/scoring.py:14-15` |
| AI-detection results, video results | `routers/analysis.py:16-17` |
| Feynman live sessions, Feynman scores | `routers/feynman.py:73,243` |
| users | `routers/auth.py:65` |

The obvious cost is data loss on restart. The hidden cost is worse: **you can never run more than
one uvicorn worker.** No scale-out, no container replicas, no surviving a crash mid-demo — two
workers would each hold their own `_score_cache` and disagree about a candidate's score. Leaderboard,
cohort analytics, growth letters and judge mode are all downstream of fixing this.

### 2. Blocking sync SDK calls inside `async def`

Verified still present:

- `scoring/ai_scorer.py:202,214` — sync `get_client()` inside `async def compute_ai_score`
- `scoring/ai_detector.py:394,404` — same, inside `async def detect_ai_content`
- `scoring/video_analyzer.py:152,160` — same, inside `async def analyze_video`

One candidate being scored freezes *every other request* for 10–30 seconds.
`get_async_client()` already exists in `ai_client.py` and is unused — the fix is three call sites
plus `await`. (`feynman.py` chat is a plain `def`, so FastAPI threadpools it; that one is
accidentally safe.)

### 3. `/api/scoring/ai/all` is a sequential for-loop

`routers/scoring.py:57-73`. 16 candidates × ~15s ≈ 4 minutes with the server unresponsive. Needs
bounded `asyncio.gather`, or a job + polling, or the Batches API (50% cheaper) for the pre-demo run.

### 4. Auth is decorative — the one thing that stops a pilot cold

`routers/auth.py`: unsalted SHA-256 password hashing; a homemade token (`user_id:timestamp:sig16`)
with **no expiry and no revocation**; the signing secret defaulted in source
(`"invisionu-hackathon-secret-2026"`); users in a dict; and `useAuth.ts:33-36` has the redirect
guard commented out. Critically, **no endpoint checks `role == "committee"`** — anyone who can reach
the API reads every applicant's essay and every score. These are minors' records.

### 5. CORS `allow_origins=["*"]` with `allow_credentials=True`

`main.py:18-24`. Browsers reject that combination outright, and it is flatly wrong once auth is real.

### 6. The mocked video path is presented as a feature

`video_analyzer.py:135-139`: even when Whisper *is* available and a `video_link` exists, the code
returns `MOCK_TRANSCRIPT` (there is a TODO where the download belongs). `is_mock` is surfaced in the
response, which is honest, but a judge asking "is that transcript real?" gets a bad answer. Either
wire real transcription (local faster-whisper) or make the UI say plainly that it is a sample.

### 7. Zero tests, zero CI

The most regression-prone code in the repo is hand-rolled JSON-fence stripping and parsing,
duplicated in four places (`_parse_ai_response`, `_parse_detection_response`, and inline in
`video_analyzer.py` and `feynman.py`). None of it is covered. `except Exception` blocks forward raw
exception text to clients as 500 detail.

### 8. Dead dependencies will inflate every image you build

`scikit-learn`, `pandas`, `numpy` in `backend/requirements.txt` are used only in `notebooks/`.
They are the heaviest thing in any Docker image — roughly 400 MB and most of the wheel-build risk —
for nothing. Split into `requirements-notebooks.txt`.

### 9. Frontend: four monolithic client components

`page.tsx` 1385 lines · `dashboard/page.tsx` 1388 · `teach/page.tsx` 842 · `auth/page.tsx` 307 —
all `"use client"`, all fetching in `useEffect` (23 `useState`/`useEffect` occurrences in the
dashboard alone), no component extraction, no shared data layer, no loading/error primitives, token
in `localStorage`. It works and it looks good. It will not survive two more features or a second
frontend contributor without constant merge conflicts.

### 10. Smaller items that will bite

- **Scoring weights duplicated in three places** as literal maps — `ai_scorer.py:169`,
  `aggregator.py:16`, `dashboard/page.tsx:31`. They will drift. One source of truth, served to the
  frontend.
- `aggregator.rank_candidates` mutates cached `CandidateScore` objects in place while ranking.
- `lib/types.ts` is hand-maintained against Pydantic models — silent drift is guaranteed. FastAPI
  already publishes an OpenAPI schema; generate the types from it.
- No `/healthz` / `/readyz` — needed by compose healthchecks, the deploy platform, and uptime pings.
- `load_dotenv()` at import time in several modules, no typed settings object. This will fight with
  container env vars over precedence.
- No `.gitattributes` — git already warns CRLF→LF on four files. A CRLF shell entrypoint inside a
  Linux container fails with an unreadable error.
- Scores are neither reproducible nor attributable: nothing records which model and prompt version
  produced a stored score.

---

## The uncommitted work is itself a risk

The working tree holds the deprecated-model migration (`ai_client.py` + five modified modules) and
the entire `docs/plan/` set, untracked, on a branch named `feat/docker-compose`. The most valuable
fix in the repo is sitting where a bad `git checkout` destroys it. Commit it today, as its own PR,
separate from Docker work — and rename or split the branch so its name matches its contents.

---

## What this means for the month

Roughly two of the four weeks is plumbing: persistence → async → auth → Docker → CI. That is not
overhead; it is the precondition for every feature in [product-plan.md](../product-plan.md). Plan
feature scope against **two** weeks of capacity, not four.

See [month-1-roadmap.md](month-1-roadmap.md) for sequencing,
[adr-001-go-python-frontend.md](adr-001-go-python-frontend.md) for the stack decision.
