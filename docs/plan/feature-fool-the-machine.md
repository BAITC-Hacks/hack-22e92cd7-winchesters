# Feature — Fool the Machine 🥈 (public AI-detection sandbox)

> A public page where anyone — judges included — pastes an essay and watches the
> stylometry engine judge it, metric by metric. Preempts the strongest Q&A
> attack ("AI detectors don't work") by showing ours is transparent math + a
> clearly-weighted qualitative layer, not a black-box verdict.
> Prerequisites: A2/A3; E4 (so the public endpoint can't reach committee data);
> `slowapi` rate limiting (shared with Arman Live AL3).

---

## Backend · S/M

**New endpoint:** `POST /api/analysis/sandbox`

- Request: `{essay_text: str (100..8000 chars), interview_text?: str,
  mode: "stats" | "full"}`.
- `mode="stats"` (default, **$0**): run `detect_language` +
  `compute_stylometry` + `compute_statistical_score` only — pure Python, no
  Claude call. Response: language, the 7 `StylometryMetrics`, the per-metric
  thresholds used (from `THRESHOLDS[lang]`), statistical score, flags.
- `mode="full"`: adds the Claude qualitative stage and the 40/60 blend —
  **rate-limited hard** (e.g. 5/hour/IP) and behind the `DEMO_KILL_SWITCH`.
  For the live demo this is the impressive mode; for a permanently public page,
  stats-only is the default.
- **Never persisted** — nothing written to `detections` (that table is for
  candidates); no PII concerns because we store nothing.
- Refactor note: `detect_ai_content` currently takes a `Candidate`; extract an
  inner `detect_ai_content_text(essay, interview)` that both the candidate path
  and the sandbox call — no logic duplication.

**Canned "AI essay" button ($0 at runtime):** pre-generate 3 fixture essays per
language (one obviously AI, one humanized-AI, one real human sample from the
synthetic dataset) and ship them as static fixtures the UI can load. Judges who
don't want to type still get the full experience; no generation cost on stage.

## Frontend · M

New page `/detector` (public link, also linked from the landing page):

- Big paste box + language auto-detect chip + "try an example" buttons (the
  3 fixtures) + Analyze.
- Results: one **card per metric** — value, a small gauge showing where it sits
  against the language-specific thresholds, and a one-sentence plain-language
  explanation ("Human writers vary sentence length; AI text is unnaturally
  even. Yours: 34.2 — very human."). The 7 explanations already exist in the
  code comments of `ai_detector.py` — surface them.
- Verdict banner with the blend formula shown explicitly: `40% × statistics +
  60% × qualitative` — transparency *is* the feature.
- In `full` mode, show Claude's flags/explanation in a separate, clearly
  labeled section.

## Demo script

Invite a judge: "paste anything — your own writing, or ask ChatGPT on your
phone to write an admissions essay." Run stats mode live (instant), then full
mode on their text. Either outcome is a win: caught = the system works;
not-caught = "and this is why statistics are only 40% of the weight, an
interview-voice comparison exists, and a human makes the final call" — which is
the honest, defensible answer.

## Done when

- Sandbox endpoint returns correct metrics for the 3 fixtures in each language
  (snapshot tests, B1 style, zero Claude calls in `stats` mode).
- Rate limit and kill switch verified.
- The page reads well on a phone (judges will open it there).
- Committee endpoints remain 403 for anonymous users (E4 regression test).

## Effort & risks

Backend S/M (mostly refactor + one endpoint), frontend M (the metric cards are
the work). Risk: judges' text in a language the thresholds don't cover —
`detect_language` falls back to English thresholds; label the result "calibrated
for KZ/RU/EN" rather than pretending universality.
