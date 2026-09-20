# Phase A — Foundations

> Four small PRs that unblock everything else. Total effort: ~1–2 days.
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
5. (Costs tokens) `POST /api/scoring/ai/c-001` returns a score — **if this 404s
   on the model name, the deprecated-model problem (A3) is already live.**

**Done when:** all five checks pass (or #5 fails *only* on the model, which we fix in A3).

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

**Files:** new `backend/config.py`; edit `backend/main.py`; add
`pydantic-settings` to `requirements.txt`; expand `backend/.env.example`.

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
1. Add `pydantic-settings` to requirements; create `backend/config.py` with the
   class above, `model_config` pointing at `backend/.env`, and a module-level
   `settings = Settings()` singleton.
2. `main.py`: replace the CORS block with `allow_origins=settings.cors_origins`;
   keep `allow_credentials=True`. For the LAN demo, `.env` will list the laptop's
   LAN origin (e.g. `http://192.168.1.42:3000`) — no code change needed.
3. Move the `load_dotenv()` calls into `config.py` (one place); delete them from
   `main.py`, `ai_scorer.py`, `ai_detector.py`.
4. Update `.env.example` documenting every key with a comment.

**Done when:** app boots reading all config through `settings`; missing
`ANTHROPIC_API_KEY` fails at startup with a clear pydantic error (not at first
request); frontend still works; grep for `os.getenv` finds hits only in `config.py`.

**Gotchas:** import order — `config.py` must not import any router. `cors_origins`
as a list from env: pydantic-settings parses JSON (`["http://..."]`) or you add a
comma-split validator; pick one and document it in `.env.example`.

**Prod note:** in production the same class reads real env vars (no `.env` file);
secrets come from the platform's secret store. Nothing changes in code.

---

## A3 — Centralize the Anthropic client + **migrate the deprecated model** · S/M

**Why (two reasons, one urgent):**
1. **The pinned model `claude-sonnet-4-20250514` is deprecated and past its
   published retirement date (2026-06-15).** All four AI modules will 404 when
   it is switched off, if they don't already.
2. Four files each build their own client and hardcode the model string in ~6
   places. One choke point = one-line model swaps forever, plus a clean seam for
   Phase F (sync→async) and the Ollama-fallback provider interface.

**Files:** new `backend/ai_client.py`; edit `ai_scorer.py`, `ai_detector.py`,
`video_analyzer.py`, `feynman.py` (remove local `_get_client()` + model strings).

**Spec — `backend/ai_client.py`:**
- `get_client() -> anthropic.Anthropic` — sync singleton (kept until F1 lands).
- `get_async_client() -> anthropic.AsyncAnthropic` — async singleton (used from F1 on).
- `MODEL = settings.anthropic_model` and `CHAT_MODEL = settings.anthropic_model_chat or MODEL`.
- Later (local-models feature) this file grows a minimal provider Protocol; do
  **not** build that now — this PR is behavior-preserving de-duplication plus
  the model swap.

**Migration notes for `claude-sonnet-4` → `claude-sonnet-5`** (from Anthropic's
migration guide — these are the ones that apply to *this* codebase):
- **Silent default change:** on Sonnet 5, omitting `thinking` runs **adaptive
  thinking by default** (on Sonnet 4 it ran without thinking). `max_tokens` caps
  *thinking + text combined*. Our Feynman chat uses `max_tokens=200` — adaptive
  thinking would eat that budget and truncate Arman's replies. **Action:** pass
  `thinking={"type": "disabled"}` explicitly on the Feynman chat/quiz calls
  (fast, cheap, persona work) and leave adaptive thinking on (with a raised
  `max_tokens`, e.g. 4000) for the scorer/detector/evaluator calls where
  judgment quality matters.
- We pass no `temperature`/`top_p`/`top_k` anywhere — good; Sonnet 5 rejects
  non-default values. Do not add them.
- No assistant prefills in the codebase — good; they 400 on Sonnet 5.
- New tokenizer: ~30% more tokens for the same text vs the 4.x family. Raise
  `max_tokens` headroom on the scorer (2000 → 4000) and re-baseline any cost
  expectations. Per-token price: $3/$15 per MTok (intro $2/$10 through 2026-08-31).

**Also in this PR (small, high value):** the model change is a natural moment to
note (not necessarily implement) that all four modules hand-strip markdown fences
and `json.loads` the reply. Anthropic now has **structured outputs**
(`output_config={"format": {"type": "json_schema", "schema": ...}}` or
`client.messages.parse(..., output_format=PydanticModel)`) which guarantees
schema-valid JSON and deletes that whole fragile parsing layer. Spec the switch
as its own follow-up PR ("A3b — structured outputs") touching `_parse_ai_response`,
`_parse_detection_response`, the quiz parser, and the Feynman scorer parser. This
directly de-risks the live demo (JSON-parse crashes are the #1 way LLM demos die).

**Done when:** exactly one module constructs clients and names models;
`grep -r "claude-sonnet-4" backend/` returns zero hits outside `config.py`
defaults/`.env.example`; a manual `POST /api/scoring/ai/c-001` succeeds on the
new model; Feynman chat replies are not truncated.

**Gotchas:** keep the PR reviewable — client dedup + model swap + the two
`thinking` decisions. Structured outputs go in the follow-up PR, not this one.

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
