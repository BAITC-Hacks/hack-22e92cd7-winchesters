# Month-1 Roadmap — and the risks nobody is tracking

> Written 2026-09-12. Horizon: four weeks to a polished, sustainable product.
> Reads on top of [codebase-assessment.md](codebase-assessment.md),
> [adr-001-go-python-frontend.md](adr-001-go-python-frontend.md),
> [phase-c-docker.md](phase-c-docker.md), [deployment-path.md](deployment-path.md).

## Capacity reality

Three people, four weeks. Plumbing (persistence → async → auth → Docker → CI) is about **two of
those weeks**. So feature scope must be planned against two weeks, not four. The corollary is in
§ "What to cut" below, and it is the most important section here.

---

## Week-by-week

### Week 1 — stop the bleeding, prove the claim
- ~~Commit the uncommitted model migration as its own PR, today.~~ **Done 2026-09-20** — landed
  as `backend/settings.py` + `backend/llm.py` from `main`, which also took the async fix and
  parallel batch scoring listed under Week 2 with it. See
  [phase-a-foundations.md § A3](phase-a-foundations.md#a3--the-single-claude-call-path--done).
- `.gitattributes`, `.dockerignore`, notebook deps split out of `requirements.txt`, `/healthz` + `/readyz`.
- Typed settings object (Phase A2) + CORS fix — prerequisite for compose env handling.
- `docker compose` up to and including the `backend` service.
- GitHub Actions: lint / test-with-mocked-Claude / docker build. **The 17 tests now in `tests/`
  make this cheap and it is still not done — highest-value item left in Week 1.**
- **Compute the pitch number** (see risk 1). Before any feature work.
- Persistence PR 1: schema + candidates off the JSON file.

### Week 2 — make it a system
- Persistence PRs 2–4: scores, detection/video results, Feynman sessions, users. Every module-global
  dict deleted. (This is what unlocks `--workers > 1`.)
- ~~Async fix (three call sites) + parallel batch scoring.~~ **Done** — arrived early, with the
  model migration. The unproved part is the concurrency test; see
  [phase-f-async.md](phase-f-async.md).
- Auth hardening: bcrypt, JWT with expiry, DB-backed users, **role gating on committee endpoints**,
  re-enable the frontend guard.
- Frontend: same-origin `/api` proxy, OpenAPI type generation, split the two biggest monoliths.
- Compose completed (frontend service + dev override). First Friday clean-machine run.

### Week 3 — the features that win
- **Arman Live** stages 1–3: understanding meter, voice, judge mode.
- **No Dead Ends** growth letters (cheap, highest emotional return per hour).
- Optional: **one** Go service — the realtime hub (see ADR-001). Only if weeks 1–2 landed on time.
- Bias perturbation test suite (risk 5) + local faster-whisper if time allows.
- Data-policy / model-card one-pager (risk 4).

### Week 4 — deploy, harden, rehearse
- Deploy to Fly + Vercel + Neon; secrets in platform storage; always-on for demo week.
- Sentry, structured logs, rate limits, budget kill switch, tested DB restore.
- **Scope freeze 5 days out.** Last 5 days: rehearsal, data, bug-fixes only. No new endpoints.

---

## What to cut — read this before planning features

Of the six features in [product-plan.md](../product-plan.md), ship **two**, and keep the rest as
roadmap slides:

| Feature | Call |
|---|---|
| **Arman Live** | **Ship.** It is the participation moment; nothing else replaces it. |
| **No Dead Ends** | **Ship.** Cheapest emotional payload in the set. |
| Fool the Machine | **Only if it is ≈1 day** — it defuses the single most likely Q&A attack. |
| Fairness Sandbox · Uncertainty Triage · local models | **Defer.** Present as named next steps. |

A credible roadmap with two finished features reads far better to a sponsor than three half-working
ones. "Here is what's next and here is why our architecture already allows it" is a strong slide;
a feature that breaks on stage is not.

---

## Risks and gaps nobody is currently tracking

### 1. The pitch's one number does not exist yet
`product-plan.md` promises "baseline screening misses X of our top-10 candidates." Both scorers and
the data already exist, so this depends on nothing — **do it in week 1.** And if the number comes
out weak, you need to know early: it might change which features are worth building. Right now the
entire pitch rests on an uncomputed figure.

### 2. Scores are neither reproducible nor attributable
The same candidate scored twice can yield different numbers (LLM nondeterminism plus adaptive
thinking), and nothing records which **model** and **prompt version** produced a stored score. Store
`model`, `prompt_version`, and the raw response alongside every score. Without it you cannot explain
a past admissions decision — which is an audit requirement — and you cannot distinguish a prompt
regression from noise.

### 3. Human-in-the-loop is implied, not enforced
The override endpoint exists, but nothing in the data model requires a committee action before a
decision is final. Make it structural: a decision record with a required human actor. That single
design choice is your answer to "did a computer reject my child?", and it is worth more than any
feature.

### 4. The legal/ethics deliverable is a document, not a slide
Applicants are minors, Kazakhstan's personal-data law applies, and the buyer is an admissions office
that will be asked hard questions. You need in writing: what data leaves the machine, retention
period, human-in-the-loop guarantee, appeal path. **Known gap to fix while writing it:** `privacy.py`
masks emails and phone numbers but **not the applicant's own name inside the essay body** — and
essays nearly always contain it. A one-page model card + data policy will impress the sponsor more
than another feature.

### 5. The fairness rubric is unmeasured
The prompt says do not penalize public-school candidates or imperfect English. Nothing verifies that
it doesn't. Cheap version: perturbation tests over the synthetic set — same essay, swap school type,
name, gender markers, language polish; assert the score moves less than N points. It is a pytest
suite, it is the strongest possible answer to the judges' hardest question, and no competing team
will have one.

### 6. There is no cost model
Universities buy predictability. One slide: "scoring one applicant costs $X; a 500-applicant cohort
costs $Y; with the Batches API, $Y/2." X is measurable today from `response.usage` on a single call.

### 7. Process, for three people in four weeks
Protect `main`; every change a PR; designer reviews Vercel previews; **weekly Friday demo to
yourselves against the compose stack, not local dev servers.** The clean-machine question gets
answered four times instead of once, on demo morning.

### 8. Bus factor on the plan itself
Fourteen-plus planning documents exist and are currently untracked. Commit `docs/` in the same pass
as the model fix. A plan that lives on one laptop is not a plan.
