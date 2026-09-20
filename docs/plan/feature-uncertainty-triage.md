# Feature — Uncertainty Triage 🥉 ("Second Reader")

> Reframe the dashboard's default sort: not "who scored highest" but **"where
> should scarce human attention go first."** The system already computes
> everything needed (baseline vs AI disagreement, per-dimension confidence,
> detection flags) — this feature turns it into a review queue.
> The pitch sentence: *"We don't rank students — we rank uncertainty. The AI's
> job is to allocate committee attention, not to decide."* This is the most
> intellectually serious line in the deck; ML-literate judges and admissions
> professionals both nod at it.
> Prerequisites: D (both score types queryable); builds on the existing
> `compare_scores()` in `aggregator.py`.

---

## The attention score

For each candidate with both a baseline and an AI score:

```
attention =
    w1 · |ai_overall − baseline_overall| / 100          # model disagreement
  + w2 · max_dimension_disagreement / 100               # sharpest single conflict
  + w3 · low_confidence_dimensions / 5                  # how much the AI hedged
  + w4 · detection_flag_count (capped at 3) / 3         # authenticity questions
  + w5 · is_borderline(overall, cutoffs=50, 70, band=±5) # near a decision boundary
```

Start with `w = (0.35, 0.2, 0.15, 0.15, 0.15)`; expose the weights in a config
dict so tuning is one edit. Every component is already computed somewhere in
the codebase — this is assembly, not new ML.

**Reasons, not just a number:** alongside the score, emit human-readable
`reasons: list[str]`, e.g. "AI and baseline disagree by 18 points on
leadership", "2 authenticity flags", "3 points below the 'recommend' cutoff".
The reasons are the feature; the number is just the sort key.

## Backend spec · S

**New endpoint:** `GET /api/scoring/triage` (committee-only, E4)

- For all candidates having both scores (compute missing baselines on the fly —
  they're free), return sorted-descending:
  `{candidate_id, name, attention_score, reasons[], ai_overall,
  baseline_overall, recommendation}`.
- Implementation in `aggregator.py` (`compute_attention(...)` pure function +
  a thin router handler). Pure math, no AI calls, fully unit-testable with
  exact-value assertions.

## Frontend spec · S/M

- Dashboard: a sort-mode toggle — "By score" (current) / **"Review queue"**.
- In review-queue mode each card shows the reason chips (max 3) instead of the
  rank number; a small flame/attention icon scaled by score.
- Candidate detail panel: a "Why flagged" section listing all reasons — this
  reuses the existing baseline-vs-AI comparison data (`/api/scoring/compare`).

## Demo script (20 seconds)

Toggle to Review queue: "the committee has 30 minutes; these five files are
where humans genuinely change the outcome — the rest, both scorers agree."
Then click one and show the disagreement detail.

## Done when

- `compute_attention` unit-tested with hand-built fixtures covering each
  component in isolation and the weighted sum.
- Queue order changes sensibly when an override is applied (override reduces
  disagreement → candidate sinks).
- Zero added AI cost (verify: no client calls on this path).

## Production note

At pilot scale this becomes the committee's daily landing page, and the weights
deserve calibration against real committee behavior (which files did humans
actually spend time on / flip decisions on). Log queue impressions + decision
flips from day one so the calibration data exists later.
