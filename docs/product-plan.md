# InVision U — Product Plan: Hackathon Win → Pilot → Production (Index)

> Owner: Almas · Created 2026-07-07 · Status: **planning**
>
> Companion to [backend-plan.md](backend-plan.md) (infrastructure). This file
> covers *what we ship and why it wins* — for the hackathon judges (inDrive)
> and for the first real customer (a university admissions office).

## The thesis

Judges reward three things in the first 3 minutes: **an emotional story, a
moment they personally participate in, and one number that proves it works.**
Universities (the actual buyers) reward **trust, auditability, and cost
predictability**. Every feature below serves one of those two audiences, and
everything is buildable with $0 beyond Claude tokens we already spend.

> **Scope revision 2026-09-12:** with ~2 of 4 weeks going to plumbing, ship **two** features
> (Arman Live + No Dead Ends) and present the rest as roadmap. Rationale and week-by-week plan in
> [month-1-roadmap.md](plan/month-1-roadmap.md).

## Feature roadmap

| Priority | Feature | Spec | Audience | Effort |
|---|---|---|---|---|
| 🥇 **Killer** | **Arman Live** — voice-first Feynman challenge, visible understanding meter, judges play from their phones, live leaderboard | [feature-arman-live.md](plan/feature-arman-live.md) | Judges (participation + emotion) | L |
| 🥈 | **Fool the Machine** — public AI-detection sandbox with transparent metric breakdown | [feature-fool-the-machine.md](plan/feature-fool-the-machine.md) | Judges (defuses the #1 attack in Q&A) | M |
| 🥈 | **No Dead Ends** — personalized growth letter for every rejected candidate | [feature-no-dead-ends.md](plan/feature-no-dead-ends.md) | Judges + applicants (emotional closer) | S/M |
| 🥉 | **Fairness Sandbox** — live admitted-class composition panel next to the weight sliders | [feature-fairness-sandbox.md](plan/feature-fairness-sandbox.md) | Universities (policy instrument) | M |
| 🥉 | **Uncertainty Triage** — rank candidates by model disagreement, not score | [feature-uncertainty-triage.md](plan/feature-uncertainty-triage.md) | Universities (systems credibility) | S/M |
| 🔧 | **Local models** — self-hosted Whisper (real video transcription, $0), embeddings (semantic voice match + cross-applicant plagiarism), optional Ollama fallback | [feature-local-models.md](plan/feature-local-models.md) | Both (privacy story + fixes a known limitation) | M/L |
| 🏁 | **Demo-day playbook** — pre-scoring, network setup, failure drills, pitch arc | [demo-day-playbook.md](plan/demo-day-playbook.md) | Us | S |
| 🏭 | **Production readiness** — async vision, cost self-sustainability, deployment, observability, security/compliance | [production-readiness.md](plan/production-readiness.md) | Universities / the company | ongoing |

## Dependency map (features ↔ infrastructure phases)

```
Arman Live ──────── needs F1/F2 (async), D (persistence for leaderboard),
                    A2 (LAN/CORS config), B (prompt-change safety net)
Fool the Machine ── needs A2/A3; E4 for public/committee separation; rate limiting
No Dead Ends ────── needs D (letters cached in DB), A3 (model routing)
Fairness Sandbox ── needs D (scores queryable), existing reweight endpoint
Uncertainty Triage─ needs D; builds on existing compare_scores()
Local models ────── needs C (containers); independent of D/E
```

**Build order that maximizes demo value per week:**

1. Week 1 — Phase A + F (infra) + **Arman Live stage 1–2** (understanding meter + voice).
2. Week 2 — Phase C1 + D (persistence) + **Arman Live stage 3–4** (judge mode + leaderboard) + Fool the Machine.
3. Week 3 — Phase E + No Dead Ends + Fairness Sandbox + Uncertainty Triage + local Whisper.
4. Demo week — playbook, rehearsals, pre-scoring, polish.

## The pitch arc (7 minutes)

1. **Problem (30s):** applications see paperwork, not people. Show one synthetic
   village kid the rule-based baseline rejects.
2. **Solution (2m):** trajectory scoring + Feynman challenge surface them. Live
   demo of Arman Live — teach by voice, watch the understanding meter climb.
3. **Trust (1.5m):** Fool the Machine — invite a judge to paste an AI essay live.
   Fairness sandbox — drag a slider, watch class composition change.
4. **Heart (1m):** No Dead Ends — show the rejection letter. "Every other
   admissions system says no and goes silent. Ours says no and hands you a map."
5. **Participation (2m):** QR code on screen. Judges teach Arman from their
   phones. Leaderboard on the projector while we take questions.

**The one number** (to compute from `notebooks/`): "baseline screening misses
X of our top-10 candidates; our pipeline recovers them."

## Pilot / production definition

- **Polished MVP (hackathon):** everything above, running on our laptops + LAN.
- **Self-sustainable pilot:** deployed on free-tier infra (see
  [production-readiness.md](plan/production-readiness.md)), one university
  admissions office running a real cohort, Claude spend under a monthly budget
  guardrail, data of minors handled per policy.
- **Production:** multi-tenant, SLA-monitored, on-prem-capable (local-model
  story), paid contract. Out of scope for now; the plan keeps doors open.
