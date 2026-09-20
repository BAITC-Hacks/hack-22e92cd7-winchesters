# Phase B — Tests & CI

> The safety net. Lands right after Phase A so every later PR (persistence,
> auth, async, prompt changes) ships with tests. Total effort: ~1–2 days.
> Prerequisites: A2 (config), A3 (the single call path — the thing we mock; **done**).
>
> **Status 2026-09-20: B1 is partly done, B2 (CI) is done.** `tests/` holds 17 offline tests and
> a `pytest.ini`, merged from `main`. They came from the FND-01/03 work and cover the call
> contract and the AI scorer — not the routers. `.github/workflows/ci.yml` now runs them plus the
> frontend build on every push and PR. What is left of this phase is router coverage: the gap
> list is under "What already exists" below.

---

## B1 — pytest scaffolding + smoke tests · M

**Why:** the riskiest work ahead (D: persistence rewrite, F: async rewrite,
prompt changes for Arman Live) all change behavior that is currently verified
only by clicking through the UI. Tests with a **mocked Claude client** make
those changes safe, free, and deterministic.

**New concepts:**
- `pytest` — test runner; auto-discovers `tests/test_*.py` (repo root, not `backend/tests/` —
  that is where they landed, and `pytest.ini` points `testpaths` there). Like `go test`.
- `fastapi.testclient.TestClient` — calls the app **in-process** (no server, no
  port). Like `httptest`.
- `conftest.py` — shared fixtures file, auto-loaded. Fixtures are pytest's DI:
  a test that declares a `client` parameter receives the object built by the
  `client` fixture.
- `monkeypatch` — pytest's built-in for swapping attributes for one test. After A3 there is
  exactly one place to patch, and it is **not** the client: stub the two functions in
  `backend.llm`. The existing tests do
  `monkeypatch.setattr(llm, "complete_json", fake)` where `fake` is an `async def` returning a
  plain dict — no fake client object, no fake response blocks, because structured outputs mean
  `complete_json` hands back a parsed dict. Patch `llm.complete_chat` the same way for Feynman.

## What already exists (read before writing any of this)

| File | Covers |
|---|---|
| `pytest.ini` | `testpaths = tests`, `asyncio_mode = auto` (so `async def` tests need no decorator) |
| `tests/test_llm_contract.py` | Model ids come from `settings`; the retired id cannot reappear; low-resource routing avoids small models; `_assert_strict_schema` rejects open objects, optional properties and bad nested arrays; every shipped `*_SCHEMA` survives it; `_text_of` finds text past a thinking block and raises when there is none; `wrap_document` attributes and marks empty artifacts; the Feynman quiz reads only the candidate's own words |
| `tests/test_scoring_pipeline.py` | `compute_ai_score` with `llm.complete_json` stubbed: shape, clamping, committee weights, recommendation vocabulary |

**Still missing, in value order:** the routers (`test_candidates.py`, `test_auth.py`), the
baseline scorer's determinism, `complete_chat` behavior for Feynman, and **B2 — CI**. Add
`requirements-dev.txt` (`pytest`, `pytest-asyncio`, `httpx`) while you are there; the test deps
are currently installed by hand and pinned nowhere.

**Files:** new `tests/conftest.py`, `tests/test_candidates.py`,
`tests/test_scoring_baseline.py`, `tests/test_auth.py`; new `requirements-dev.txt`.

**Spec — `conftest.py` fixtures:**

| Fixture | Provides |
|---|---|
| `client` | `TestClient(app)` with a dummy `ANTHROPIC_API_KEY` env so imports don't fail |
| `mock_llm` | `monkeypatch.setattr(backend.llm, "complete_json", ...)` with an `async def` returning a fixture **dict** (not a JSON string, not a fake response object) — and the same for `complete_chat` returning a string |
| canned fixtures | one valid JSON string per parser: scorer response (5 dimensions), detection response, Feynman quiz, Feynman evaluation — stored under `backend/tests/fixtures/` so prompt-format changes update one file |

**Test list (initial):**

| Test | Asserts |
|---|---|
| `test_list_candidates` | 200; 16 items; first has `id == "c-001"` |
| `test_get_candidate_404` | unknown id → 404 |
| `test_create_candidate` | 201; returned id matches `c-\d{3}`; **use a tmp copy of candidates.json or roll back** (until D removes file writes) |
| `test_baseline_deterministic` | baseline score for `c-001` twice → identical numbers (pure function — assert exact values) |
| `test_baseline_weights` | custom weights change `overall_score` as expected |
| `test_register_login_me` | register → login → `/me` happy path; wrong password → 401 |
| `test_ai_score_mocked` | with `mock_anthropic`, `POST /api/scoring/ai/c-001` returns parsed dimensions from the fixture; **no network** |
| ~~`test_ai_parse_garbage`~~ | **Drop this one.** It documented the hand-rolled fence-stripping, which no longer exists — the API enforces the schema. The useful replacement: `complete_json` raising (timeout, refusal) must leave the candidate *out* of `/ai/all` rather than cached as a zero, which is what `routers/scoring.py` now does. |

**Done when:** `pytest` green locally in <10s (currently ~3s for 17 tests); disconnecting from
the internet changes nothing (proof no real API calls); the create-candidate test does not
permanently mutate `backend/data/candidates.json`.

**Gotchas:**
- The candidates router caches the JSON in a module-global — tests that create
  candidates must reset `_candidates_cache` (fixture teardown) until Phase D
  deletes it. This annoyance is itself an argument for D.
- Auth's in-memory `_users` leaks between tests — reset it in a fixture too.

**Prod note:** this same mock seam is how you'll build the prompt-regression
"golden set" later (see production-readiness § LLM quality ops).

---

## B2 — GitHub Actions CI · **done**

> Landed 2026-09-20, ahead of C1 rather than after it — there is no Postgres yet, so there was
> nothing to wait for.

**Why:** every PR gets an automatic green/red; nobody merges a broken parser the
night before the demo.

**Shipped as `.github/workflows/ci.yml`**, two jobs on every push to `main` and every PR, with
`concurrency` cancelling superseded runs:

1. **backend** — Python 3.14 (matching local), pip cached on both requirement files,
   `pip install -r backend/requirements.txt -r requirements-dev.txt`, `python -m pytest -q`.
2. **frontend** — Node 24, `npm ci`, `npm run build` (which type-checks the whole app, so it is
   the TypeScript gate as well), then `npm run lint`.

Plus `requirements-dev.txt` at the repo root — the test deps were installed by hand and pinned
nowhere until now.

**Three decisions worth knowing before you change it:**

- **No `ANTHROPIC_API_KEY` in the job env.** The spec above called for a dummy key; it turned out
  not to be needed, and leaving it out is better: if someone ever writes a test that really calls
  the API, it fails in CI instead of quietly spending tokens on every push.
- **Lint is `continue-on-error: true`.** `npm run lint` currently exits 1 — one error
  (`react-hooks/set-state-in-effect` in `src/lib/useAuth.ts:26`) and 27 warnings. Gating on it
  today would make every PR red for a reason unrelated to the PR. **Fix that error, then delete
  the line**; the comment in the workflow says the same.
- **No `ruff` yet.** The spec wanted it, but there is no lint config in the repo at all
  (`pyproject.toml` does not exist), so adding a linter means first agreeing a config and fixing
  whatever it finds across ~3,300 LOC. That is its own PR, not a rider on CI.

**Still to add, when the thing it depends on exists:** after Phase D, a `services: postgres:16`
block with a health check, `DATABASE_URL`, and alembic migrations before pytest.

**Done when:** a PR shows checks; deliberately breaking a test turns it red; total runtime
< 3 minutes. **Verify the red case on the first PR** — a workflow that has never failed has not
been tested.

**Gotchas:** Windows-developed, Linux-CI — watch path separators and any `PowerShell`-isms in
scripts; keep scripts cross-platform (Python, not shell). `.gitattributes` (added alongside this)
normalizes line endings so a CRLF script never reaches a Linux runner or container.
