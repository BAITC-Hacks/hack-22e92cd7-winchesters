# LED-12 demo click audit

Date: 2026-09-27. Mock demo day: 2026-09-28. The question for every click on
the demo path (STAGE2_IMPROVEMENT_PLAN.md §8, in the order before / fairness /
inside / committee / after / model card) is: does it call a model, and what
happens when no key is set.

Setting: backend on a copy of the dev database with `ANTHROPIC_API_KEY`,
`OPENAI_API_KEY` and `ELEVENLABS_API_KEY` empty and `ASR_ENABLED=0`, frontend
from `next build` + `next start`. The whole path was clicked through in the
browser: no 5xx responses, and a fresh login produced no console errors.
`tests/test_led12_demo_offline.py` pins the same behaviour, with a model
client that fails the test if anything reaches it.

**Source** says where the figures on screen come from:
**DB** means stored rows. **Cache** means a checked-in fixture, labelled as
one. **Det.** means deterministic code with no model. **Live** means a model call.

## How "no key" works now

- `backend/llm.py` raises `ModelUnavailable` before it builds a request
  whenever no usable key is set. The `.env.example` placeholder
  `your-anthropic-api-key-here` counts as no key. It used to send every
  fallback path to the network, where it got a 401. The gate lives in the one
  place every call passes through, so no fallback can reach the network by
  accident.
- Clicks on the demo path never depend on a model. The one exception is the
  Scenario Lab, which asks `/api/feynman/mode` first and replays the cached
  transcript.
- Endpoints that only make sense live answer **503** with "nothing was
  scored", never 500 or 502. Nothing is recorded, because nothing was
  attempted.

## Clicks

| Step | Page → click | Endpoint | Model call? | Source | Without a key |
|---|---|---|---|---|---|
| — | `/auth` → Sign in (committee demo) | `POST /api/auth/login` | no | DB | 200. The dev DB used to answer 401, see below |
| before | `/dashboard` load | `POST /api/scoring/rank?scorer=baseline`, `GET /api/ledger`, `GET /api/fairness/audit?source=synthetic` | no | Det. / DB / Det. (synthetic, labelled) | 200 |
| before | Completeness ↔ AI score toggle | `POST /api/scoring/rank?scorer=ai` | no (stored runs only) | DB | 200 `[]`, shown as "No candidate has a stored AI score yet", never as zeros |
| before | Weight sliders | none (client-side reweight) | no | Det. | — |
| before | Open candidate card | `GET /api/overrides/{id}`, `/reason-codes`, `GET /api/feynman/score/{id}`, `GET /api/committee/pre-brief/{id}` (only if a ledger exists) | no | DB | 200. No ledger: "Unavailable — nothing was scored", and neither the 404 nor the 409 is requested |
| before | Application tab → Run consistency check | `POST /api/analysis/ai-detection/{id}` | no (LED-02 shim) | Det. | 200 |
| before | Application tab → Analyze Video Presentation | `POST /api/analysis/video-analysis/{id}` | only with a transcript and a key | — | 200 `no_transcript` / `unavailable`: "nothing was scored", no numbers |
| before | Committee Card / Interviewer Brief / Growth Map tabs | ledger from `GET /api/ledger`, `GET /api/ledger/rubric` | no | DB | c-001: banner "Illustrative worked example — not from this applicant", with every quote tagged. Others: "Unavailable — nothing was scored" |
| fairness | Fairness Audit → Blind / Informed | none | no | — | — |
| fairness | Fairness Audit → attribute audit | `GET /api/fairness/audit` | no | Det. (synthetic, labelled) | 200 |
| fairness | Fairness Audit → Ledger health | from `GET /api/ledger` | no | DB | The illustrative example is not counted. With no cached run: "Unavailable — nothing was scored" |
| fairness | Swap and rescore → Run probe | `POST /api/fairness/probe/{id}?live=true` | tried only with a key | Det. baseline | 200 `fallback_demo`, chip "Fallback · deterministic baseline, no model call", notice "no model API key on this server" |
| inside | Interviewer Brief (pre-brief) | `GET /api/committee/pre-brief/{id}` | no | DB | 200 with `ledger_provenance`; quotes from the illustrative example are tagged |
| inside | Application tab → Show cached demo transcript | `GET /api/feynman/demo` | no | Cache (INP-03) | 200, "Cached demo transcript" |
| inside | `/teach` load (applicant) | `GET /api/feynman/topics`, `GET /api/feynman/mode` | no | Det. | `mode.live=false`, with the notice "Live AI student unavailable on this server" |
| inside | `/teach` → View cached demo transcript | `GET /api/feynman/demo` | no | Cache | 200, "Cached demo transcript: replayed from a fixture" |
| inside | `/teach` → start / chat / finish a live session | `POST /api/feynman/start` / `chat` / `finish` | yes | Live | Not reached from the UI without a key. Direct calls answer 503 ("view the cached demo transcript instead"); chat/finish used to answer 502 |
| committee | Committee Card → expand competency | none | no | DB | quotes tagged "Illustrative, not from this applicant" on c-001 |
| committee | Committee Card → Override → Record | `POST /api/overrides/{id}` | no | DB (append-only) | 201 |
| committee | `/decision-memo` load, ru/kk | `GET /api/committee/decision-memo/c-001?locale=` | no | DB | 200, provenance banner, "Example levels (not AI)" instead of "AI drafted", quotes tagged. No ledger: "Unavailable", not a red 409 |
| committee | `/decision-memo` → PDF | `GET …/pdf` | no | DB | 200 PDF. The provenance line is printed near the top, wrapped instead of cut off |
| committee | `/decision-memo` → Sign | `POST …/signatures/{role}` | no | DB | 201 |
| committee | `/evaluation` load | `GET /api/fairness/evaluation`, `GET /api/fairness/cohort-probe` | no (`live=false`) | Det. baseline on a synthetic fixture | 200, chip "Cached demo · deterministic baseline, no model call", line "Figures below come from the deterministic baseline …" |
| after | Growth Map tab | ledger | no | DB | as the Committee Card |
| close | `/model-card` | `GET /api/fairness/historical/status`, then the card only if one was ingested | no | DB | "Unavailable — nothing was scored: no historical evaluation has been ingested" (the 404 is not requested) |
| close | `/funder-memo` | `GET /api/fairness/heldout/status`, then the memo | no | DB | "Unavailable — nothing was scored" |
| close | `/reproducibility` | `GET /api/fairness/heldout/status`, then the replay | no | DB | "Unavailable — nothing was scored" |
| — | `/` → submit application | `POST /api/candidates/` | no | DB | 201 |

These endpoints can call a model but no demo click reaches them. Without a key
they answer:

| Endpoint | Before | Now |
|---|---|---|
| `POST /api/scoring/ai/{id}`, `/ai/all` | 500 (the call failed and was stored as a failed run) | 503 "AI scoring unavailable … Nothing was scored." Nothing is stored. With a key, a real upstream failure still gives 500 and a failed run, as before |
| `GET /api/fairness/evaluation?live=true` | fell back after trying the model | falls back without trying; `fallback_reason: "no model API key on this server"` |
| `GET /api/fairness/cohort-probe?live=true` | fell back after trying | `status: "fallback"`, no call |
| `POST /api/fairness/scorer-versions/{v}/publish` | 503 after trying | 503, no call |
| `POST /api/feynman/chat`, `/finish` | 502 | 503, "view the cached demo transcript instead" |

## The c-001 contradiction

The worked example (`backend/ledger/fixtures/ledger_example.json`) was written
for a fictional applicant `a-7f3c2e91`. None of its four quotes appears in any
of c-001's texts. Only the Kazakh one points at a source c-001 does not have
(`written_presentation`), and that is why the clash was visible.

What we chose: the example stays attached to c-001 so that the demo has one
ledger to show. It is presented as what it is:

- `backend/ledger/provenance.py` derives the kind of ledger from `model_judge`,
  which the seed sets to `hand-authored`. The kind is either
  `illustrative_example` or `cached_run`. Nothing new is stored, so no
  migration was needed.
- The memo, pre-brief and PDF carry `ledger_provenance`. The card, brief and
  Growth Map show the banner, and every quote from the example carries
  "Illustrative, not from this applicant".
- The cohort Ledger health leaves it out.
- c-001 still has no written presentation, and nothing was invented to make
  the quote "fit".

A cached run for c-001 replaces the example automatically (`seed_demo_ledger`).

## The dev-database 401

In the dev database, the `committee@invisionu.edu` row dates from 2026-09-21,
before FND-05. It still held an unsalted SHA-256 hex digest, which argon2
rejects (`InvalidHashError` → 401). The old `seed()` skipped any email that
already existed, so `init` never fixed it.

Now `seed()` does this, and only under DEMO_MODE and only for that one
account: it verifies the demo password, rehashes when verification fails, and
resets the role if it has drifted. A healthy row is left byte-for-byte
unchanged, so a second `init` is a no-op. The fix was checked on a copy of the
dev database: the first `init` printed "demo committee account repaired", and
the login then worked.

**The dev database itself has not been touched.** To fix it, run
`python -m backend.db init` once.

## No schema change

- Provenance is derived from the existing `model_judge` column.
- The account repair is a data fix done in seed.
- The status endpoints only read `model_runs`.

So there is no revision 0005, and 0001–0004 are unchanged.

## What is left

The ledger cache (`backend/ledger/fixtures/cache/`) is still empty, because
building it takes live calls and this task forbade them. So c-001 is the only
applicant with a ledger, and that ledger is illustrative. One command with a
funded key closes this:

```
python -m backend.ledger.cache && python -m backend.db init
```

Also still open:

- The memo's "Frozen provenance → Model" hash is a sha256 of the model label.
  For the example, that label is `hand-authored`. This is known from the
  2026-09-27 audit, and the memo now says above it that the ledger is
  illustrative.
- A stale token left in the browser from an older database makes the first
  `/api/auth/me` answer 401 (it shows in the console) before the redirect to
  login. Log in fresh on the demo machine.
