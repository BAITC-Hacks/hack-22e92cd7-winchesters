# InVision U — AI-Powered Admissions Platform

> **The best way to find a leader is to watch them teach.** We built an AI-assisted evaluation system that measures what applications can't: patience, empathy, and the ability to make complex things simple.

[Demo Video](https://drive.google.com/drive/folders/1ntxiZNCST5MVuq4X8uppDuZCcNnJLgPc?usp=sharing) | [Architecture](docs/architecture.md)

---

## The Problem

Standard university applications see **paperwork, not people**. Talented students from rural areas get overlooked because they can't "sell themselves" in a form. Meanwhile, AI-generated essays make written applications unreliable.

## Our Solution

A hybrid evaluation platform where **AI assists, humans decide**:

| Feature | What It Does |
|---------|-------------|
| **Feynman Teaching Challenge** | Candidate teaches a concept to an AI "student" (4-8 exchanges). AI intentionally misunderstands once to test patience. Quiz measures knowledge transfer. Scores clarity, patience, empathy, adaptability. Quiz answers shown transparently — not a black box. |
| **Trajectory Scoring** | Measures how far you've come, not where you started. Village student → university = more growth credit. |
| **Multi-lingual Stylometry** | 7 math-based text metrics (no AI) detect essay fraud in Kazakh, Russian, and English with language-specific thresholds. |
| **Dual Scoring Pipeline** | Rule-based baseline (instant, free) + Claude AI (nuanced). Both run independently, results compared. |
| **Configurable Rubric** | Committee adjusts scoring weights via sliders. Rankings update live. Your proprietary metrics, our engine. |
| **Fairness Audit** | Dashboard panel showing score distribution by recommendation category. Proves the system evaluates merits, not background. |
| **Hidden Gem Filter** | Surfaces candidates with low formal metrics but exceptional teaching ability or growth signals. |
| **Committee Override** | Human-in-the-loop: override any AI dimension score with a note. Overall score recomputes automatically. |
| **Sparse Profile Handling** | Missing data shifts weight to essay + teaching challenge instead of penalizing. |
| **Video Presentation Analysis** | Compares video transcript voice with essay voice for authenticity. Extracts motivation signals. Supports Whisper API or manual transcript. |
| **Auth System** | Register/login for applicants. Committee demo account included. Candidate ID linked to user account automatically. |
| **PII Anonymization** | Names, emails, phone numbers stripped before any data reaches Claude AI. |

---

## Team

| Name | Role | Contact |
|------|------|---------|
| Rauan Salkenov | Developer | [Telegram](https://t.me/regularmusician) · [GitHub](https://github.com/raursq) |
| Arman Sagnaev | Product Designer | [Telegram](https://t.me/armashq) |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| Backend | Python 3.12, FastAPI, Pydantic v2 |
| AI | Claude Sonnet 4 (scoring, detection, Feynman chat), OpenAI Whisper (video transcription, optional) |
| Non-AI | Pure Python signal extraction, rule-based baseline, statistical stylometry |

---

## Architecture

```
  Auth (Register/Login)
          |
Applicant Portal          Teaching Challenge          Admissions Dashboard
      |                         |                           |
      v                         v                           v
  [Application Form]    [Chat with AI Student]    [Candidate Rankings]
  [Video + Transcript]   [Quiz + Scoring]          [Evaluation Settings]
      |                         |                  [Fairness Audit]
      +-------------------------+                  [Video Analysis]
                |                                  [Committee Override]
         [FastAPI Backend]
        /        |        \
   [Signal      [Feynman    [Video
    Extractor]   Engine]     Analyzer]
   [Baseline    [AI Chat]   [Whisper/
    Scorer]     [Quiz]       Mock]
   [AI Scorer]  [Evaluator]
   [AI Detector]
   [PII Anonymizer]
        |            |
   [Claude API]  [OpenAI API]
```

> Detailed diagrams: [docs/architecture.md](docs/architecture.md)

---

## Quick Start

```bash
# Clone
git clone https://github.com/raursq/invision-u-winchesters.git
cd invision-u-winchesters

# Backend
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env   # add ANTHROPIC_API_KEY (required for live AI calls)
python3 -m backend.db init             # create/upgrade the SQLite database and load the demo data
python3 -m uvicorn backend.main:app --port 8000

# After pulling changes that touch backend/migrations/, run `python3 -m backend.db init` again.
# The API refuses to start on an outdated database and prints this command.
# `python3 -m backend.db reset` deletes the local database and rebuilds it from the seed.

# Frontend (requires Node 20+)
cd frontend && npm install && npx next dev --port 3000
```

Open [http://localhost:3000](http://localhost:3000)

---

## Scoring Dimensions

| Dimension | Weight | Signal |
|-----------|--------|--------|
| Leadership Potential | 25% | Roles, projects, initiative |
| Motivation & Values | 25% | Essay voice, personal drive |
| Growth Trajectory | 20% | Delta: where you are − where you started |
| Academic Strength | 15% | GPA, achievements, languages |
| Communication | 15% | Essay clarity, sentence structure |

> **Weights are defaults.** The admissions committee can adjust them via the Evaluation Settings panel on the dashboard. Rankings update live — plug in your proprietary rubric and the system adapts instantly.

---

## Ethical AI & Fairness

- **PII stripped** before any data reaches AI (names, emails, phones redacted)
- **No demographic bias** — school type used only for growth delta, never as success predictor
- **Human-in-the-loop** — all AI labels are advisory; committee overrides any score
- **Explainable** — every score has evidence quotes, reasoning, and confidence level
- **"Sparse Profile" handling** — missing data shifts weight to essay + teaching challenge instead of penalizing

## Baseline Improvement

Dual scoring proves AI value: rule-based baseline (instant, free) vs Claude AI (nuanced). Dashboard shows "AI Insight" per candidate — what traditional screening would miss.

## Known Limitations

- LLM may hallucinate justifications → mitigated by requiring exact quote evidence
- Stylometry may false-positive on strong writers → only 40% weight (60% Claude qualitative)
- Kazakh stylometry baselines are less established than English/Russian
- Video analysis runs only on the applicant's own transcript; without one it returns `no_transcript` and scores nothing. ASR is off (ElevenLabs Scribe v2 only, behind `ASR_ENABLED` + `ELEVENLABS_API_KEY`; never Whisper)
- Candidates and accounts are stored in SQLite; scores, detection results and Feynman sessions are still in memory and reset on restart (moving in FND-04 PR 3/4)

---

## Project Structure

```
├── backend/
│   ├── main.py                # FastAPI entry point
│   ├── routers/               # API endpoints (auth, candidates, scoring, analysis, feynman)
│   ├── scoring/               # Signal extraction, baseline, AI scorer, detector, aggregator, video analyzer
│   ├── db/                    # SQLite via SQLModel: tables, repositories, seed (`python -m backend.db init`)
│   ├── migrations/            # Alembic migrations
│   ├── privacy.py             # PII anonymization
│   └── data/                  # Seed dataset (16 candidates, 3 languages); the local .db lives here, gitignored
├── frontend/src/app/
│   ├── page.tsx               # Landing + Application Form (5 steps)
│   ├── auth/page.tsx          # Sign In / Sign Up
│   ├── teach/page.tsx         # Feynman Teaching Challenge
│   └── dashboard/page.tsx     # Admissions Dashboard
├── docs/                      # Architecture diagrams
└── notebooks/                 # Validation analysis
```

## License

MIT
