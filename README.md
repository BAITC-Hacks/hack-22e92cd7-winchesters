# hack-22e92cd7-winchesters
Hackathon team repository for Winchesters

# InVision U — AI-Assisted Admissions Platform

> **AI finds the evidence, the committee decides.** Every competency level the
> system shows comes with the applicant's own words as the quote, against the
> university's behavioural rubric, and says so plainly when there is no evidence
> rather than scoring it low.

[Demo Video](https://drive.google.com/drive/folders/1ntxiZNCST5MVuq4X8uppDuZCcNnJLgPc?usp=sharing) | [Architecture](docs/architecture.md) | [Task board](docs/STAGE2_TASK_BOARD.md) | [Demo click audit](docs/plan/led-12-demo-click-audit.md)

---

## The Problem

Standard university applications see **paperwork, not people**. Talented
students from rural areas get overlooked because they can't "sell themselves"
in a form, and the usual automated fixes (keyword counts, GPA weights, AI-text
detectors) penalise exactly the applicants who write in Kazakh or in an
additional language.

## What the platform does

| Feature | What it does |
|---------|--------------|
| **Evidence ledger** (LED-03/04) | For each competency: a BARS level (High / Normal / Weak / No evidence), the verbatim quote it rests on, the indicator it matches and the source (essay, written presentation…). "No evidence" is its own state, never a low score. |
| **Committee card, Interviewer Brief, Growth Map** (LED-05/11) | Three views of the same stored ledger: what the committee rates, what the interviewer should probe, what the applicant may later see. |
| **Committee override** (COM-01) | A committee member changes one competency's level with a mandatory reason code. Overrides are appended, never written over the AI level, and the history shows who changed what. |
| **Decision memo** (COM-04) | Russian / Kazakh memo and PDF with the evidence, overrides, bias probe, frozen version hashes and committee signatures. |
| **Fairness audit** (FAIR-07) | Share of each group rated High, per competency, with 95% bootstrap intervals and a 0.8 review line. Groups with n < 10 are marked "Not enough data". |
| **Swap and rescore** (FAIR-06) | Changes name, region, school type, language and speech style and checks whether any level flips. |
| **Written presentation** (INP-01) | 150–300 words in any language; the scored input instead of video. Video transcripts are auxiliary and never scored without the applicant's own transcript. |
| **Teaching Challenge / Scenario Lab** (INP-03) | The applicant teaches a concept to an AI "student". Results are shown as "observed in simulation" with weight 0: they never move a score or a rank. |
| **Completeness view** (LED-01) | How much material exists per dimension, so the committee sees a candidate assessed on four sources apart from one assessed on an essay alone. It is not a merit score. |
| **Blind / Informed** (FAIR-01) | Candidate context is hidden from the committee view while evidence is reviewed. |

**What scoring never uses:** school type, region, GPA, family income, gender,
application language, essay length or manner of speech.
`tests/test_no_demographics_in_scoring.py` fails the build if any of them moves
a score. The old AI-authorship detector was removed (LED-02). It flagged
non-native writing, and nothing calibrated for Kazakh exists.

---

## Current state (2026-09-27, before the mock demo day)

The demo works **without any API key**. Every click reads from the database, a
cache labelled as one, or a deterministic baseline. Live-only endpoints answer
503 "nothing was scored" instead of an error. Checked on a copy of the dev
database with every model key empty: 445 tests pass, the whole demo path
produces no 5xx responses and no console errors
([audit](docs/plan/led-12-demo-click-audit.md)).

Not done yet:

- **Ledger cache: 0 of 16 applicants.** Only c-001 has a ledger, and it is the
  hand-authored LED-03 worked example for a fictional applicant. It is shown
  as *"Illustrative worked example — not from this applicant"*, every quote is
  tagged, and it is not counted in cohort figures. The other 15 show
  "Unavailable — nothing was scored". With a funded `ANTHROPIC_API_KEY`:
  `python -m backend.ledger.cache && python -m backend.db init`.
- **The attribute-grouped fairness audit on the dashboard uses 200 synthetic
  profiles.** It is labelled "demonstrates the method, not evidence". On the
  real database it has no levels yet, so it shows no figures.
- **Evaluation harness, swap-and-rescore and cohort probe run the
  deterministic baseline** ("no model call" chip). Their 0% flip rate says
  nothing about the AI scorer yet.
- **Model card, funder memo and reproducibility** show "Unavailable" until
  inVision U's historical data arrives.
- **7 of 9 rubric scales are drafts** until the Talent Craft BARS arrive with
  the extended methodology.

---

## Team

| Name | Role | Contact |
|------|------|---------|
| Rauan Salkenov | Developer | [Telegram](https://t.me/regularmusician) · [GitHub](https://github.com/raursq) |
| Almas Magzumov | Developer | — |
| Arman Sagnaev | Product Designer | [Telegram](https://t.me/armashq) |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 (design tokens in `globals.css`) |
| Backend | Python 3.12+, FastAPI, Pydantic v2, SQLModel + Alembic on SQLite |
| AI | Claude via `backend/llm.py`, the only place a model is called. Model ids come from `backend/settings.py` (`MODEL_JUDGE`, `MODEL_EXTRACT`, `MODEL_CHAT`). With no key, the call is refused before a request is built. |
| ASR | Off by default. ElevenLabs Scribe v2 only, behind `ASR_ENABLED` + `ELEVENLABS_API_KEY` |
| Non-AI | Completeness reference, fairness statistics, deterministic fallbacks |

Prompt and rubric content is hashed and locked in
`backend/ledger/versions.lock.json`. CI fails on any change without a version bump.

---

## Architecture

```
Applicant Portal            Teaching Challenge           Admissions Dashboard
 (application +              (AI student, weight 0,       (committee / admin only)
  written presentation)       cached demo transcript)
        |                           |                              |
        +---------------------------+------------------------------+
                                    |
                            [FastAPI backend]
     ledger/ (extract -> rate -> ATOLA, versions)   routers/ (auth, candidates, ledger,
     scoring/ (completeness, fairness audit)                  overrides, committee, fairness,
     committee_memo / prebrief / probe bank                   feynman, analysis, scoring)
     privacy.py (PII stripped before any model call)
                                    |
                 [SQLite: applicants, artifacts, ledger runs,
                  overrides, audit log, signatures]
                                    |
                     llm.py -> Claude API (optional for the demo)
```

> Detailed diagrams: [docs/architecture.md](docs/architecture.md)

---

## Quick Start

### Docker (only Docker Desktop needed)

```bash
docker compose up --build
```

Open [http://localhost:3000](http://localhost:3000) and sign in with
`committee@invisionu.edu` / `demo2026`. The database is created and seeded
on first start (the `backend-data` volume); `docker compose down -v` wipes it.
No API key is needed. To add one, copy `backend/.env.example` to
`backend/.env`: compose reads it at run time. Ports can be changed with
`FRONTEND_PORT` / `BACKEND_PORT`. The browser only talks to the frontend,
which proxies `/api` to the backend, so the same stack also works from a
phone on the LAN at `http://<laptop-ip>:3000`.

### Local dev (hot reload)

```bash
# Clone
git clone https://github.com/raursq/invision-u-winchesters.git
cd invision-u-winchesters

# Everything at once (venv, backend + frontend deps, backend/.env)
make install
make db-init        # create/upgrade the SQLite database and load the 16 demo applicants
make dev            # backend on :8000, frontend on :3000
```

Or by hand:

```bash
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env   # AUTH_SECRET is required; ANTHROPIC_API_KEY is optional for the demo
python -m backend.db init
python -m uvicorn backend.main:app --port 8000
cd frontend && npm install && npx next dev --port 3000
```

Open [http://localhost:3000](http://localhost:3000). The demo committee account
is `committee@invisionu.edu` / `demo2026`, seeded while `DEMO_MODE=1`.

- After pulling changes that touch `backend/migrations/`, run
  `python -m backend.db init` again. The API refuses to start on an outdated
  database and prints this command.
- `python -m backend.db reset` deletes the local database and rebuilds it from the seed.
- On the demo machine, log in fresh: a token left from an older database gives
  one 401 in the console before the redirect to login.
- Tests: `python -m pytest`.

---

## Ethical AI & Fairness

- **PII stripped** before any text reaches a model (names, emails, phones redacted).
- **No background in the score.** Protected attributes are collected for
  auditing only, and no scorer imports them.
- **Levels, never averages.** Levels are counted per group and never turned
  into a 0–100 number.
- **Human in the loop.** AI levels are advisory. Overrides are recorded with a
  reason, and signatures are on the memo.
- **Explainable.** Every level rests on a verbatim quote from the applicant's
  own text. No evidence is shown as "no evidence", not as a weak result.
- **Honest labels.** Synthetic, cached, illustrative and fallback figures are
  labelled as such. A page with nothing behind it says "Unavailable —
  nothing was scored".

## Known Limitations

- The ledger cache is empty (see *Current state*). Until it is built, the
  committee card is shown only on the illustrative c-001 example.
- 7 of 9 rubric scales are drafts. The COM-06 probe bank is provisional.
- No historical data yet (expected from Oct 5), so there is no agreement or
  fairness evidence on real outcomes. The model card stays empty.
- The Kazakh evaluation relies on the same pipeline as Russian and English.
  Cross-lingual agreement has so far only been measured on the deterministic
  baseline.
- No transcription call is implemented. Video analysis runs only on the
  applicant's own transcript.

---

## Project Structure

```
├── backend/
│   ├── main.py                # FastAPI entry point
│   ├── llm.py                 # the single Claude client (refuses without a key)
│   ├── ledger/                # evidence ledger pipeline, cache builder, version locks
│   │   └── fixtures/          # LED-03 worked example; cache/ holds built ledgers
│   ├── routers/               # API endpoints
│   ├── scoring/               # completeness reference, fairness audit, synthetic cohort
│   ├── committee_*.py         # decision memo, pre-brief, probe bank
│   ├── db/                    # SQLModel tables, repositories, seed (`python -m backend.db init`)
│   ├── migrations/            # Alembic migrations (0001–0004)
│   ├── privacy.py             # PII anonymization
│   └── data/                  # Seed dataset (16 applicants, 3 languages); the local .db is gitignored
├── frontend/src/app/
│   ├── page.tsx               # Landing + application form
│   ├── auth/                  # Sign in / sign up
│   ├── teach/                 # Teaching Challenge (applicant)
│   ├── dashboard/             # Admissions dashboard (committee)
│   ├── decision-memo/         # Committee decision memo + PDF
│   ├── evaluation/            # Scorer evaluation harness
│   └── model-card/, funder-memo/, reproducibility/
├── tests/                     # pytest suite
├── docs/                      # plan, task board, research, architecture
└── notebooks/                 # validation analysis
```

## License

MIT
