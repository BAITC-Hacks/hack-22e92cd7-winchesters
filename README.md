# InVision U — AI-Powered Admissions Platform

> **The best way to find a leader is to watch them teach.** We built an AI-assisted evaluation system that measures what applications can't: patience, empathy, and the ability to make complex things simple.

[Demo Video](#) | [Architecture](docs/architecture.md) | [Live App](#)

---

## The Problem

Standard university applications see **paperwork, not people**. Talented students from rural areas get overlooked because they can't "sell themselves" in a form. Meanwhile, AI-generated essays make written applications unreliable.

## Our Solution

A hybrid evaluation platform where **AI assists, humans decide**:

| Feature | What It Does |
|---------|-------------|
| **Feynman Teaching Challenge** | Candidate teaches a concept to an AI "student." Scores patience, clarity, empathy — skills you can't fake. |
| **Trajectory Scoring** | Measures how far you've come, not where you started. Village student → university = more growth credit. |
| **Multi-lingual Stylometry** | 7 math-based text metrics (no AI) detect essay fraud in Kazakh, Russian, and English. |
| **Configurable Rubric** | Committee adjusts scoring weights via sliders. Your proprietary metrics, our engine. |
| **Hidden Gem Filter** | Surfaces candidates with low formal metrics but exceptional teaching ability or growth signals. |

---

## Team

| Name | Role | Contact |
|------|------|---------|
| Rauan Salkenov | Developer | [GitHub](https://github.com/raursq) |
| Arman Sagnaev | Product Designer | |
| Aidar Islyamov | UX/UI Designer | |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| Backend | Python 3.12, FastAPI, Pydantic v2 |
| AI | Claude Sonnet 4 (scoring, detection, Feynman chat) |
| Non-AI | Pure Python signal extraction, rule-based baseline, statistical stylometry |

---

## Architecture

```
Applicant Portal          Teaching Challenge          Admissions Dashboard
      |                         |                           |
      v                         v                           v
  [Application Form]    [Chat with AI Student]    [Candidate Rankings]
  [Video Link]           [Quiz + Scoring]          [Evaluation Settings]
      |                         |                  [Fairness Audit]
      +-------------------------+                  [Committee Override]
                |
         [FastAPI Backend]
          /          \
   [Signal Extractor]  [Feynman Engine]
   [Baseline Scorer]   [AI Student Chat]
   [AI Scorer]         [Quiz Evaluator]
   [AI Detector]       [Teaching Scorer]
   [PII Anonymizer]
          |
     [Claude API]
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
export ANTHROPIC_API_KEY=your_key
python3 -m uvicorn backend.main:app --port 8000

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
- Video presentations are link-only (no audio/video processing)
- In-memory cache — scores reset on restart

---

## Project Structure

```
├── backend/
│   ├── main.py                # FastAPI entry point
│   ├── routers/               # API endpoints (candidates, scoring, analysis, feynman)
│   ├── scoring/               # Signal extraction, baseline, AI scorer, detector, aggregator
│   ├── privacy.py             # PII anonymization
│   └── data/                  # Synthetic dataset (15 candidates, 3 languages)
├── frontend/src/app/
│   ├── page.tsx               # Landing + Application Form (6 steps)
│   ├── teach/page.tsx         # Feynman Teaching Challenge
│   └── dashboard/page.tsx     # Admissions Dashboard
├── docs/                      # Architecture diagrams
└── notebooks/                 # Validation analysis
```

## License

MIT
