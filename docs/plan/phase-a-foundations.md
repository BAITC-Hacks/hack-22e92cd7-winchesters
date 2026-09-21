# Phase A — Foundations

> Four small PRs that unblock everything else. Total effort: ~1–2 days.
> **Status 2026-09-20: A3 is done, A2 is half-done — read the notes on each before starting.**
> Prerequisites: none. Read the Go-dev primer in [../backend-plan.md](../backend-plan.md) first.

---

## A1 — Stand up the local dev environment · S

**Why:** you can't verify anything until the app runs on your machine; this is
also your first contact with the Python run model.

**Steps (Windows / PowerShell):**

```powershell
# from repo root
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # prompt now shows (.venv)
pip install -r backend/requirements.txt
Copy-Item backend/.env.example backend/.env
# edit backend/.env → put the real ANTHROPIC_API_KEY
python -m backend.db init             # SQLite schema + 16 demo records; rerun after pulling migrations
python -m uvicorn backend.main:app --reload --port 8000
```

Second terminal:

```powershell
cd frontend
npm install
npx next dev --port 3000
```

**Verify:**
1. http://localhost:8000/docs loads (auto-generated Swagger — your API map).
2. `GET /api/candidates/` returns 16 candidates.
3. `POST /api/auth/login` with `committee@invisionu.edu` / `demo2026` returns a token.
4. http://localhost:3000 renders; dashboard loads candidates.
5. (Costs tokens) `POST /api/scoring/ai/c-001` returns a score. The deprecated-model
   404 that used to break this is fixed (A3); a failure here now means the key, not the model.
6. `python -m pytest` → 17 passed, and passes with the network off.

**Done when:** all six checks pass.

**Troubleshooting table:**

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: backend` | uvicorn started from inside `backend/` | run from repo root |
| `pip` installs but imports fail | venv not activated | activate, reinstall |
| `401 authentication_error` from Anthropic | key missing/typo in `backend/.env` | fix key; `load_dotenv()` reads `backend/.env` only if CWD is right — see A2 |
| Port 8000 busy | stale process | `Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess \| Stop-Process` |

---

## A2 — Typed config + CORS fix · S

**Why:** configuration is scattered `os.getenv(...)` calls and a hardcoded auth
secret; `main.py` sets `allow_origins=["*"]` together with
`allow_credentials=True`, which browsers **reject** per the CORS spec and which
is insecure anyway. One typed settings object fixes both and is the foundation
for Docker, DB, auth, and the LAN demo config.

**New concept:** `pydantic-settings` — a class whose fields are populated from
environment variables / a `.env` file, validated at startup. Think
`envconfig`/`viper`, but it crashes loudly at boot if required config is missing
(which is what you want).

> **Partly overtaken 2026-09-20.** `backend/settings.py` now exists and owns the AI-related
> config (model ids, token caps, concurrency, timeouts, `DEMO_MODE`) — but with plain `os.getenv`
> and defaults, **not** pydantic-settings, so nothing is validated at boot and a missing
> `ANTHROPIC_API_KEY` still fails at the first request. What remains of A2: the CORS fix, the
> auth/database/frontend fields, and the decision whether to convert `settings.py` to a
> `pydantic-settings` class or leave it. Do **not** create `config.py` beside it — one settings
> module, whichever shape wins.

**Files:** `backend/settings.py` (exists — extend it rather than adding `config.py`); edit
`backend/main.py`; add `pydantic-settings` to `requirements.txt` if the class shape wins; expand
`backend/.env.example`.

**Spec — `Settings` fields:**

| Field | Type | Default | Used by |
|---|---|---|---|
| `anthropic_api_key` | str | *(required)* | A3 client |
| `anthropic_model` | str | `claude-sonnet-5` | A3 |
| `anthropic_model_chat` | str | `""` (falls back to `anthropic_model`) | model routing (prod-readiness) |
| `openai_api_key` | str | `""` | video_analyzer (until local Whisper) |
| `auth_secret` | str | *(required — no baked-in default!)* | Phase E |
| `access_token_expire_minutes` | int | `1440` | Phase E |
| `database_url` | str | `""` | Phase D |
| `cors_origins` | list[str] | `["http://localhost:3000"]` | main.py |
| `whisper_url` | str | `""` | local-models feature |
| `ai_provider` | str | `"anthropic"` | Ollama fallback (feature) |

**Steps:**
1. Decide the shape first: keep `backend/settings.py` as module-level constants, or convert it to
   a `pydantic-settings` class. The class buys boot-time validation (a missing
   `ANTHROPIC_API_KEY` crashes at startup with a clear error instead of at the first scoring
   request) at the cost of touching every `settings.MODEL_JUDGE`-style reference. Either way it
   stays one module.
2. Add the fields the table above lists and `settings.py` does not have yet: `auth_secret`,
   `access_token_expire_minutes`, `database_url`, `cors_origins`, `openai_api_key`,
   `whisper_url`. (`DEMO_MODE` and the model/runtime fields already exist.)
3. `main.py`: replace the CORS block with `allow_origins=settings.CORS_ORIGINS`;
   keep `allow_credentials=True`. For the LAN demo, `.env` will list the laptop's
   LAN origin (e.g. `http://192.168.1.42:3000`) — no code change needed.
4. `settings.py` already calls `load_dotenv()`; delete the remaining calls from `main.py` and
   anywhere else that still has one.
5. Update `.env.example` documenting every key with a comment.

**Done when:** app boots reading all config through `settings`; a missing `ANTHROPIC_API_KEY`
fails at startup rather than at first request; frontend still works; grep for `os.getenv` finds
hits only in `settings.py`.

**Gotchas:** import order — `settings.py` must not import any router (it currently imports
nothing from the app, keep it that way). `cors_origins` as a list from env: pydantic-settings
parses JSON (`["http://..."]`) or you add a comma-split validator; pick one and document it in
`.env.example`.

**Prod note:** in production the same module reads real env vars (no `.env` file);
secrets come from the platform's secret store. Nothing changes in code.

---

## A3 — The single Claude call path · **done**

> **Landed 2026-09-20, and not as specced below.** This task was implemented twice in parallel:
> `backend/ai_client.py` on this branch, and `backend/settings.py` + `backend/llm.py` on `main`
> (task FND-01 of [../STAGE2_TASK_BOARD.md](../STAGE2_TASK_BOARD.md)). The merge kept main's and
> deleted `ai_client.py`. The section is kept for the migration reasoning, which is still the
> reason the code looks the way it does — but **`backend/llm.py` is the source of truth now.**

**Why it was urgent:** the pinned model `claude-sonnet-4-20250514` was deprecated and past its
published retirement date (2026-06-15), and four files each built their own client and hardcoded
the model string in ~6 places.

**What shipped:**

- `backend/settings.py` — every model id and runtime knob, from env, with working defaults:
  `MODEL_JUDGE=claude-opus-5` for rating and scoring, `MODEL_EXTRACT=MODEL_CHAT=claude-sonnet-5`
  for extraction and persona turns, plus `MAX_CONCURRENT_LLM_CALLS`, timeouts, retries and
  `MODEL_FOR_LOW_RESOURCE` (Kazakh and code-switched text never routes to a small model).
- `backend/llm.py` — two entry points and nothing else:
  `await llm.complete_json(prompt, schema, system=..., model=...) -> dict` and
  `await llm.complete_chat(messages, system=..., model=...) -> str`. Async (`AsyncAnthropic`),
  capped by a shared `asyncio.Semaphore`, JSON constrained by the API rather than parsed out of
  markdown fences, and applicant text wrapped by `llm.wrap_document(text, source, doc_id)`.
- `ai_scorer.py`, `ai_detector.py`, `video_analyzer.py`, `feynman.py` — no clients, no model
  strings, no fence stripping. Each owns a `*_SCHEMA` dict instead of a parser.
- `anthropic>=1.7,<2` in `backend/requirements.txt`.

So this one module also closed the A3b structured-outputs follow-up, **F1** (async — see
[phase-f-async.md](phase-f-async.md)) and **FND-06** (prompt-injection firewall).

**The two `thinking` decisions, which still apply** (they are the reason `complete_chat` looks
different from `complete_json`):

- On Sonnet 5 and Opus 5, omitting `thinking` runs **adaptive thinking by default**, and
  `max_tokens` caps *thinking + text combined*. A persona turn capped at `MAX_TOKENS_CHAT=400`
  can therefore spend its whole budget on reasoning and come back with **no text block at all**,
  at which point `_text_of` raises. `complete_chat` passes `thinking={"type": "disabled"}` for
  exactly this reason — do not remove it without raising the budget.
- Judgement calls keep adaptive thinking on and pay for it with `MAX_TOKENS_JSON=4096`.

**Still true, do not undo:** we pass no `temperature`/`top_p`/`top_k` anywhere (Sonnet 5 and
Opus 5 reject non-default values) and there are no assistant prefills (they 400).

**Not done, and now the open half of this task:** `EFFORT_JUDGE` / `EFFORT_EXTRACT` in
`settings.py` default to empty, so no `effort` is sent at all. They were left unverified against a
funded key. Pick levels deliberately — `high` is the API default when the parameter is omitted, so
the current behavior is "high everywhere", which is not obviously what a 16-candidate cohort run
wants paying Opus rates.

---

## A4 — Trim dead dependencies · S

**Why:** `scikit-learn`, `pandas`, `numpy` sit in `backend/requirements.txt` but
(verify!) are used only by `notebooks/validation_analysis.py`. They add minutes
to installs and ~500 MB to the future Docker image.

**Steps:**
1. Verify: `grep -rE "import (numpy|pandas|sklearn)|from (numpy|pandas|sklearn)" backend/`
   → expect zero hits.
2. Move the three packages to a new `notebooks/requirements.txt`.
3. Fresh venv, `pip install -r backend/requirements.txt`, boot the app, run the
   smoke checks from A1.

**Done when:** app runs on the slimmed requirements; notebook still documented
as `pip install -r notebooks/requirements.txt`.

**Gotchas:** trust the grep, not the assumption — if anything in `backend/`
imports pandas transitively, keep it and note why.
