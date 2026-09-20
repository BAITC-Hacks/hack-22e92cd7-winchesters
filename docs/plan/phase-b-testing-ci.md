# Phase B — Tests & CI

> The safety net. Lands right after Phase A so every later PR (persistence,
> auth, async, prompt changes) ships with tests. Total effort: ~1–2 days.
> Prerequisites: A2 (config), A3 (central AI client — the thing we mock).

---

## B1 — pytest scaffolding + smoke tests · M

**Why:** the riskiest work ahead (D: persistence rewrite, F: async rewrite,
prompt changes for Arman Live) all change behavior that is currently verified
only by clicking through the UI. Tests with a **mocked Claude client** make
those changes safe, free, and deterministic.

**New concepts:**
- `pytest` — test runner; auto-discovers `backend/tests/test_*.py`. Like `go test`.
- `fastapi.testclient.TestClient` — calls the app **in-process** (no server, no
  port). Like `httptest`.
- `conftest.py` — shared fixtures file, auto-loaded. Fixtures are pytest's DI:
  a test that declares a `client` parameter receives the object built by the
  `client` fixture.
- `monkeypatch` — pytest's built-in for swapping attributes for one test. After
  A3 there is exactly one place to patch: `backend.ai_client.get_client` /
  `get_async_client`.

**Files:** new `backend/tests/__init__.py`, `conftest.py`,
`test_candidates.py`, `test_scoring_baseline.py`, `test_auth.py`,
`test_ai_mocked.py`; new `requirements-dev.txt` (`pytest`, `httpx`).

**Spec — `conftest.py` fixtures:**

| Fixture | Provides |
|---|---|
| `client` | `TestClient(app)` with a dummy `ANTHROPIC_API_KEY` env so imports don't fail |
| `mock_anthropic` | a fake client object whose `messages.create(...)` returns a canned response object (`.content[0].text` = fixture JSON); installed via `monkeypatch` on `backend.ai_client` |
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
| `test_ai_parse_garbage` | mock returns non-JSON → endpoint returns 500 with a clear detail, not a stack trace (documents current behavior; structured outputs will change this) |

**Done when:** `pytest` green locally in <10s; disconnecting from the internet
changes nothing (proof no real API calls); the create-candidate test does not
permanently mutate `backend/data/candidates.json`.

**Gotchas:**
- The candidates router caches the JSON in a module-global — tests that create
  candidates must reset `_candidates_cache` (fixture teardown) until Phase D
  deletes it. This annoyance is itself an argument for D.
- Auth's in-memory `_users` leaks between tests — reset it in a fixture too.

**Prod note:** this same mock seam is how you'll build the prompt-regression
"golden set" later (see production-readiness § LLM quality ops).

---

## B2 — GitHub Actions CI · S

> Do after C1 exists so the workflow can include a Postgres service container.

**Why:** every PR gets an automatic green/red; nobody merges a broken parser the
night before the demo.

**File:** new `.github/workflows/ci.yml`.

**Spec — jobs:**

1. **backend** (ubuntu-latest):
   - checkout; setup Python 3.12; cache pip.
   - `pip install -r backend/requirements.txt -r requirements-dev.txt`.
   - env: `ANTHROPIC_API_KEY=test-dummy`, `AUTH_SECRET=test-secret` (imports need
     them; tests never call out).
   - `ruff check backend/` (add `ruff` to dev deps — fast linter, gofmt-like).
   - `pytest`.
   - After D: add `services: postgres:16` with health check; set `DATABASE_URL`;
     run alembic migrations before pytest.
2. **frontend** (optional, cheap): `npm ci && npm run build` in `frontend/` —
   catches TS errors.

**Done when:** a PR shows checks; deliberately breaking a test turns it red;
total runtime < 3 minutes.

**Gotchas:** Windows-developed, Linux-CI — watch path separators and any
`PowerShell`-isms in scripts; keep scripts cross-platform (Python, not shell).
