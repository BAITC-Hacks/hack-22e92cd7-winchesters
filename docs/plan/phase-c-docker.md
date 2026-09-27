# Phase C — Docker Compose (revised 2026-09-12)

> **This revision supersedes the earlier two-stage plan** (C1 Postgres now, C2 full stack "near
> demo time"). Decision changed because: three people now need identical environments, the
> local-model sidecars are coming, and "works on a clean machine" must be provable weekly rather
> than discovered on demo morning.
>
> The original objection was correct and is preserved — naive full containerization kills hot
> reload. It is solved below with the base + override pattern instead of by deferring.

**Goal:** on a machine with only Docker Desktop installed, `docker compose up` produces a working
app with seeded data. And the everyday dev loop still hot-reloads.

---

## Service topology

| Service | Image / build | Purpose | Notes |
|---|---|---|---|
| `db` | `postgres:16-alpine` | Postgres | named volume `pgdata`, healthcheck `pg_isready`, host port from `${POSTGRES_PORT:-5433}` |
| `backend` | build `backend/Dockerfile` | FastAPI | `depends_on: db (service_healthy)`, port 8000 |
| `frontend` | build `frontend/Dockerfile` | Next.js | `depends_on: backend (service_healthy)`, port 3000 |
| `whisper` | profile `local-models` | faster-whisper sidecar | opt-in; multi-hundred-MB pull |
| `adminer` | profile `dev-tools` | DB browser GUI | useful while learning SQLAlchemy |
| `seed` | profile `seed`, reuses backend image | one-shot data load | see decision (f) |
| `redis` | profile `jobs` | job durability | only when Phase F3 needs it |

---

## The decisions, and why

### (a) Two files: `docker-compose.yml` + `docker-compose.override.yml`

Compose merges the override automatically when it is present.

- **Base** = production-shaped: built images, no source mounts, `next start`, `uvicorn` with no `--reload`.
- **Override** = dev: bind-mount `./backend`, `uvicorn --reload`, bind-mount frontend, `next dev`,
  publish the DB port.

**Why:** the single biggest failure mode of "dockerize everything" is that hot reload dies and
developers quietly stop using compose — at which point the compose file rots and fails on demo day.
This gives both modes with no flag to remember, and the base file is what CI and deploy use, so
**what you test is what you ship**. CI runs `docker compose -f docker-compose.yml` (no override).

### (b) One `.env` at repo root; never baked into an image

Compose passes it with `env_file` / `environment`. Ship `.env.example` with every key.

**Why:** image layers are extractable by anyone who can pull the image, so a secret in a layer leaks
permanently. Keeping config external is also what makes one image run in dev, staging and prod —
the whole point of containers.

**Wrinkle to fix first:** the backend calls `load_dotenv()` at import time in several modules and
reads a separate `backend/.env`. Container env vars and dotenv will fight over precedence.
Consolidate to one root `.env` plus a typed settings object (Phase A2) *before* wiring compose.

### (c) Backend image: `python:3.12-slim`, requirements copied before source

- Copy `requirements.txt` → `pip install` → *then* copy `backend/` — so a code change does not
  invalidate the dependency layer. This turns a 3-minute rebuild into a 5-second one.
- **Drop `scikit-learn`, `pandas`, `numpy` into `requirements-notebooks.txt` first.** This single
  change removes ~400 MB and most of the wheel-build risk from the image. Also resolves a version
  trap: the local venv is Python **3.14** and those packages are pinned to 3.14-era versions, which
  will not resolve cleanly on a 3.12 base.
- Non-root user, `EXPOSE 8000`, `WORKDIR /app` with the package at `/app/backend` — the repo uses
  absolute imports (`from backend.routers import …`), so `backend.main:app` only resolves when the
  working directory is the *parent* of `backend/`. Getting this wrong is a classic 20-minute bug.
- **No `--reload` and no `--workers` in the base CMD.** Put a comment in the compose file: workers
  must stay at 1 until Phase D removes the in-process caches, or two workers will hold separate
  `_score_cache` dicts and report different scores for the same candidate. Someone will otherwise
  "optimize" this.

### (d) Frontend image: multi-stage, `output: "standalone"`

Set `output: "standalone"` in `next.config.ts` so the runtime stage copies `.next/standalone` +
`.next/static` rather than all of `node_modules` — roughly 1.2 GB → ~180 MB.

The decision that matters: **`NEXT_PUBLIC_API_URL` is inlined at build time**, so any image built
with it is welded to one API host. Two options:

1. Pass it as a build arg — simple, but you rebuild per environment, and the demo laptop's IP
   becomes a build input. Fragile.
2. **Switch the frontend to a same-origin `/api` rewrite** → the browser never knows the API host,
   one image runs anywhere, and the frontend container proxies server-side to `http://backend:8000`.

**Recommend option 2.** It is the same change the frontend wants anyway for CORS and cookie-auth
reasons (see [adr-001](adr-001-go-python-frontend.md)), so it pays twice — and it lets you stop
publishing port 8000 publicly at all.

### (e) Healthchecks everywhere + `depends_on: condition: service_healthy`

Add `GET /healthz` (process up) and `GET /readyz` (DB reachable) to the backend first.

**Why:** plain `depends_on` waits for container *start*, not readiness. Without healthchecks the
backend boots before Postgres accepts connections and crashes — a flake that will absolutely happen
on a cold laptop on demo morning. The same endpoints then serve the deploy platform and UptimeRobot.

### (f) Seeding is an explicit one-shot, not an entrypoint side effect

`docker compose run --rm backend python -m backend.seed` (or a `seed` profile service).

**Why not on startup:** idempotency is genuinely hard to get right, it slows every boot, and an
entrypoint that mutates data is the last thing you want pointed at a pilot database holding real
applicants. Seeding should be a deliberate act you can read in shell history.

### (g) `.dockerignore` is not optional

Exclude `node_modules`, `.next`, `.venv`, `.git`, `__pycache__`, `notebooks`, `.idea`. Without it the
build context is hundreds of MB and Docker Desktop on Windows crawls. Note `frontend/public/assets`
holds several multi-MB PNGs — they belong in the image, but should go through `next/image`
optimization rather than being served raw.

### (h) Windows specifics (this is a Windows-first team)

- Docker Desktop needs the **WSL2 backend**.
- Host port **5433** for Postgres by default, to avoid clashing with a native install.
- If Next.js hot reload misbehaves over a bind mount, set `WATCHPACK_POLLING=true` in the override.
- Add `.gitattributes` (`* text=auto eol=lf`, `*.ps1 text eol=crlf`) **before** any shell script
  enters the repo. A CRLF entrypoint inside a Linux container fails with an unreadable error.

### (i) What deliberately stays out

- **No nginx/Traefik locally** — the deploy platform terminates TLS; a local proxy is complexity with
  no local payoff.
- **No Ollama by default** — multi-GB pull; behind the `local-models` profile only.
- **No Redis** until Phase F3 actually needs durable jobs.
- **No k8s manifests.** See [deployment-path.md](deployment-path.md) for why.

---

## Landing sequence (one PR each)

1. **Prep** (no compose yet): `.dockerignore`, `.gitattributes`, split notebook deps out of
   `requirements.txt`, `output: "standalone"`, `/healthz` + `/readyz`.
2. **`db` service** + `adminer` profile. Verify: `down` then `up -d`, data persists.
3. **`backend/Dockerfile`** + backend service. Verify: smoke-check every endpoint against the container.
4. **`frontend/Dockerfile`** + same-origin `/api` rewrite + frontend service. Verify: the stack works
   with `NEXT_PUBLIC_API_URL` unset entirely.
5. **`docker-compose.override.yml`** for dev hot reload, plus a `make up` / `up.ps1` one-liner and a
   rewritten README quickstart.

**Done when:** a teammate whose machine has only Docker Desktop runs two commands and gets the app
with seeded candidates — *and* the dev loop still hot-reloads both sides.

**Standing practice:** every Friday, run the app from the base compose file (not from local dev
servers) and click through the demo script. "Does it work on a clean machine" gets answered four
times, not once.
