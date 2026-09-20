# InVision U — Backend Hardening Plan (Index)

> Owner: Almas · Created 2026-07-07 · Status: **in progress — Phase A3 and F1/F2 have landed**
>
> Goal: take the hackathon MVP to a **self-sustainable pilot / production-ready product**.
> This file is the index for the *infrastructure* work. The product/feature roadmap
> (Arman Live etc.) lives in [product-plan.md](product-plan.md).

---

## ✅ Resolved 2026-09-20: the deprecated model, and where the AI code now lives

Every AI call used to pin `claude-sonnet-4-20250514`, deprecated with a retirement date of
2026-06-15 that had already passed. That is fixed and merged.

**It did not land the way [Phase A3](plan/phase-a-foundations.md#a3--the-single-claude-call-path--done)
specified.** Two implementations were written in parallel — `backend/ai_client.py` on this branch,
and `backend/settings.py` + `backend/llm.py` on `main` (task FND-01 of
[STAGE2_TASK_BOARD.md](STAGE2_TASK_BOARD.md)) — and the merge kept main's. `ai_client.py` is
deleted. **Read `backend/llm.py` before touching any AI call site**; anything below that still
says `ai_client` is describing a file that no longer exists.

The surviving implementation is wider than A3 asked for:

| File | Owns |
|---|---|
| `backend/settings.py` | Model ids and runtime knobs, read from env with working defaults, named nowhere else. `MODEL_JUDGE=claude-opus-5`; `MODEL_EXTRACT` and `MODEL_CHAT` = `claude-sonnet-5`. `MODEL_FOR_LOW_RESOURCE` pins Kazakh and code-switched text to the strongest model. |
| `backend/llm.py` | The one path every call takes: `complete_json(prompt, schema, ...)` and `complete_chat(messages, system, ...)`. Async, capped by a shared semaphore, JSON constrained by the API's structured outputs, applicant text wrapped in `<document>` tags. |

That single module closes A3, the A3b structured-outputs follow-up, F1 (async) and FND-06
(prompt-injection firewall) together. The SDK pin moved with it: `anthropic>=1.7,<2`.

---

## Read first (added 2026-09-12)

| Doc | What |
|---|---|
| [codebase-assessment.md](plan/codebase-assessment.md) | Honest audit of what's strong, what's broken, ranked by product cost |
| [adr-001-go-python-frontend.md](plan/adr-001-go-python-frontend.md) | Decision: one Go service behind a contract, AI core stays Python, frontend stays Next.js |
| [month-1-roadmap.md](plan/month-1-roadmap.md) | Four-week sequencing, what to cut, and the untracked risks |
| [deployment-path.md](plan/deployment-path.md) | CI → CD → hosting; why not Kubernetes |

Note: [phase-c-docker.md](plan/phase-c-docker.md) was **revised 2026-09-12** — full-stack compose
is now week 1, not "near demo time", using a base + dev-override split.

## How to use this plan

- Each task is sized **one PR**. Every task has: Why → New concepts (with Go
  analogies) → Files → Steps → Done-when checklist → Gotchas → Production notes.
- Effort: **S** = a few hours, **M** = a day, **L** = multi-day.
- Detailed specs are one file per phase in [`docs/plan/`](plan/).

## Phase map

| Phase | File | What | Effort |
|---|---|---|---|
| **A — Foundations** | [phase-a-foundations.md](plan/phase-a-foundations.md) | Dev env, typed config, CORS fix, ~~central AI client + model migration~~ **(A3 done)**, dead deps | S–M |
| **B — Tests & CI** | [phase-b-testing-ci.md](plan/phase-b-testing-ci.md) | pytest harness with mocked Claude, GitHub Actions | M |
| **C — Docker** | [phase-c-docker.md](plan/phase-c-docker.md) | **Revised:** full-stack compose in week 1 (base + dev override), Postgres included | M |
| **D — Persistence** | [phase-d-persistence.md](plan/phase-d-persistence.md) | SQLAlchemy 2.0 (sync) + Alembic + Postgres; kill JSON file + all in-memory caches | L |
| **E — Auth hardening** | [phase-e-auth.md](plan/phase-e-auth.md) | bcrypt, real JWT with expiry, DB users, role gating | M |
| **F — Async & performance** | [phase-f-async.md](plan/phase-f-async.md) | ~~AsyncAnthropic, parallel batch scoring~~ **(F1/F2 done)**, background jobs | S–M |

## Dependency graph & recommended PR order

```
A ──┬──> B (tests) ──────────────────────────┐
    ├──> F1/F2 (async fix — independent)     │  every later PR ships with tests
    └──> C1 (Postgres) ──> D (persistence) ──┴──> E (auth) ──> C2 (full compose)
```

**PR order:** A1 → A2 → A3 (model fix!) → A4 → B1 → F1 → F2 → C1 → B2 → D1…D6 → E1…E4 → C2.

F1/F2 are pulled early: highest value-per-hour, self-contained, and they are a
hard prerequisite for the Arman Live judge mode (concurrent sessions).

## Why this is mandatory for the product plan

Each feature in [product-plan.md](product-plan.md) depends on specific phases:

| Feature | Dies without |
|---|---|
| Arman Live judge mode (concurrent phones) | **F1/F2** — today one blocking Claude call freezes the whole server |
| Leaderboard, cohort analytics, growth letters | **D** — in-memory dicts vanish on restart |
| Phones on venue Wi-Fi | **A2** — CORS origins + configurable API host |
| Public sandbox next to committee dashboard | **E4** — role gating |
| Prompt edits the night before demo | **B** — mocked-Claude tests catch JSON-parse regressions |
| "Runs on any laptop" | **C** — one-command bring-up |

## Python/FastAPI primer for a Go developer

Read once; every phase file assumes these.

| Concept | What it is | Go analogy | The gotcha |
|---|---|---|---|
| **venv** | Per-project isolated interpreter + packages; must be *activated* | vendoring, but for the interpreter | `pip install` without activating pollutes global Python |
| **pip + requirements.txt** | Dependency list | `go.mod`, but transitive deps unpinned | No lockfile by default; pin versions |
| **asyncio event loop** | `async def` runs cooperatively on **one thread**; `await` yields | goroutines, but cooperative & single-threaded | A blocking call inside `async def` freezes **all** requests (the Phase F bug) |
| **FastAPI `def` vs `async def`** | `def` endpoints run in a threadpool (blocking OK); `async def` runs on the loop (blocking NOT OK) | `def` = own thread; `async def` = "I promise not to block" | The AI endpoints are `async def` but call a blocking SDK |
| **Pydantic models** | Validate/parse JSON at the boundary (`models.py`) | structs + `encoding/json` tags + validation | This repo is Pydantic **v2**; v1 tutorials online differ |
| **`Depends()`** | FastAPI constructs a value (DB session, current user) per request and injects it | middleware + `context.Value`, type-safe | This is how DB sessions and auth get injected; tests override it |
| **SQLAlchemy 2.0 + Alembic** | ORM + schema migrations | GORM + golang-migrate | Two API styles exist online; use **2.0** only |
| **pytest + monkeypatch/overrides** | Test runner; swap real deps for fakes | `testing` + interface stubbing | Tests must never call the real Anthropic API |

**Run model:** absolute imports (`from backend.routers import …`) mean uvicorn
is always started from the **repo root**: `python -m uvicorn backend.main:app`.

## Definition of done — every PR

- [ ] App boots from repo root; `pytest` green locally and in CI (once B lands).
- [ ] New/changed behavior covered by a test that **mocks Claude** (zero real API calls in tests).
- [ ] No new `os.getenv` outside `settings.py`; no new hardcoded model strings (they belong in `settings.py`, read via `llm.py`); no new module-level cache dicts (post-D).
- [ ] Response models unchanged unless intentional — the frontend must not break silently.
- [ ] PR description: what, why, how verified.
