# Deployment Path — CI, CD, hosting, and the Kubernetes question

> Companion to [phase-c-docker.md](phase-c-docker.md). Written 2026-09-12.
> Principle: **one image, three environments, config outside the image.**

---

## The Kubernetes question, answered up front

**No Kubernetes. Not this month, probably not this year.**

You have three services and one database. Kubernetes buys multi-node scheduling, self-healing, and
declarative rollouts — none of which you need — and costs a control plane, manifests or Helm charts,
an ingress controller, secret management, and roughly a month of learning that is not product work.
For a pilot with one university, a single container host is the correct architecture.

**Revisit when** you have ≥2 paying tenants, a contractual SLA, or genuinely need multiple backend
replicas under load. By then it is mostly a config change, because you will already have images in a
registry — which is the actual portable asset. Building images now *is* the k8s preparation.

---

## Stage 1 — CI (week 1). Highest leverage infra in the whole plan.

GitHub Actions, on pull request and on `main`:

| Job | What | Why |
|---|---|---|
| `lint` | ruff + `tsc --noEmit` + eslint | catches the cheap half of review |
| `test` | pytest with **Claude fully mocked** | a CI that spends API tokens gets switched off within a week — zero real calls, ever |
| `build` | `docker build` both images | Dockerfile rot is silent otherwise; half the value of CI is here |
| `audit` | `pip-audit` + `npm audit --omit=dev` | you are handling minors' data |

Plus branch protection on `main`.

**Why this first:** it is what lets three people merge quickly without fear during the week before
demo. Everything else in this document is optional; this is not.

## Stage 2 — CD (weeks 2–3). Build, push, deploy one host.

**Registry: GHCR** (`ghcr.io/<org>/<repo>-backend`). Free for the repo, no extra account, and
`GITHUB_TOKEN` already has push permission. **Tag with the git SHA**, not only `latest` — without an
immutable tag you have no rollback target.

**Recommended hosting split:**

| Piece | Choice | Why |
|---|---|---|
| Backend | **Fly.io** or **Railway** | Docker-native, deploys the exact image you built, private networking to the DB, generous free/hobby tier |
| Frontend | **Vercel** | Next-native, and a preview URL per PR is how the designer reviews without a local setup |
| Postgres | **Neon** or **Supabase** free tier | ~0.5 GB is plenty for a cohort; managed snapshots included |

Deploy step: `flyctl deploy --image ghcr.io/...@sha256:...` (or a Railway/Render deploy hook).
Run `alembic upgrade head` as a **release command, not an app-start hook** — a migration racing N
booting containers corrupts schema state.

**Two caveats that will bite on demo day:**

1. **Free tiers sleep on idle.** A 30-second cold start in the middle of the pitch is a disaster.
   Either pay ~$5 for one month of always-on, or warm it with a scheduled ping for demo week.
2. **Secrets are platform secrets.** `ANTHROPIC_API_KEY` goes in Fly/Vercel secret storage, never in
   the repo, never in an image layer. Rotate the current key before the repo is ever made public.

**Alternative worth naming — the single-VPS path.** A €5 Hetzner box + `docker compose` + Caddy for
automatic TLS + a GitHub Actions SSH deploy step. Cheapest, most control, and **your compose file is
literally the deploy artifact** — nothing new to learn beyond Phase C. Cost: you own patching,
backups, and uptime. If the team would rather own the box than learn a PaaS, this is a legitimate
choice, not a worse one.

## Stage 3 — Before any public URL exists (week 4)

Non-negotiable once strangers can reach it:

- **Per-IP rate limits** (slowapi) on every unauthenticated endpoint. A public AI endpoint without
  rate limiting is a bill waiting to happen.
- **Budget kill switch**: the `usage_log` table + daily budget env var already specced in
  [production-readiness.md](production-readiness.md). Guest/sandbox endpoints return a friendly 503
  past the cap.
- **Sentry** in both apps, release tagged with the git SHA.
- **Structured JSON logs** with a request id; log model + token usage + latency on every AI call.
- **UptimeRobot** on `/readyz`.
- **Nightly `pg_dump`** — and **restore it once**, before you need to. An untested backup is a rumour.

## Stage 4 — Deferred

Kubernetes, multi-tenancy (`org_id` scoping), on-prem packaging. All trigger-based, none date-based.
See [production-readiness.md](production-readiness.md) § Multi-tenancy — the schema is already
designed not to make that retrofit painful.

---

## Environments

| Env | Frontend | Backend | DB | Config source |
|---|---|---|---|---|
| `local` | compose (`next dev` via override) | compose | compose `db` | root `.env` |
| `preview` | Vercel per-PR | Fly staging app | Neon branch DB | platform secrets |
| `prod` | Vercel prod | Fly prod app | Neon main | platform secrets |

Three configurations, one image, one compose file that CI proves still works.
