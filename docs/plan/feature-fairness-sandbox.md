# Feature — Fairness Sandbox 🥉 (live class-composition panel)

> The weight sliders already re-rank candidates live. This feature adds the
> missing half: **as the committee drags weights, show what the admitted class
> would look like.** Fairness stops being an audit tab and becomes a knob you
> can feel. This is the feature that impresses *universities* — it turns an
> ideological argument ("are we fair to rural kids?") into an instrument.
> Prerequisites: D (scores queryable with weights), existing
> `/api/scoring/reweight`; E4 (committee-only).

---

## Backend spec · S/M

**New endpoint:** `POST /api/scoring/cohort-stats`

- Request: `{weights: ScoringWeights, scorer: "baseline"|"ai", top_k: int = 20}`.
- Logic: recompute overall per candidate with the given weights (reuse
  `recompute_overall` — no rescoring, no AI calls, pure math over persisted
  dimension scores), take the top-K, and aggregate:

| Response field | Definition |
|---|---|
| `school_type_distribution` | counts within top-K, bucketed: `advantaged` (private/international/lyceum/gymnasium/specialized) vs `standard` (public) vs `underserved` (village/rural) — reuse the buckets implicit in `SCHOOL_ADVANTAGE` |
| `underserved_share` | % of top-K from underserved schools — the headline number |
| `avg_growth_delta` | mean growth delta within top-K |
| `hidden_gems_in_topk` | count matching the existing Hidden Gems criteria |
| `borderline` | the 3 candidates just below the cut (ids + deficit) — makes the cut human |
| `baseline_comparison` | same aggregates under **default** weights, so the panel can show deltas |

- Performance: pure in-memory math over ≤ a few hundred rows — target <50 ms so
  slider-drag polling feels live.

**Data honesty note:** school type is a proxy, and the panel must label it as
such ("distribution by school type — proxy for access to resources"). We never
use demographics; that's already a project principle — keep it visible in the UI copy.

## Frontend spec · M

In the dashboard's Evaluation Settings panel, add a **Class Composition** card
beside the sliders:

- Stacked bar: top-K composition by bucket, animating as sliders move
  (debounce slider events ~150 ms before calling the endpoint).
- Big number: `underserved_share` with an up/down delta vs default weights.
- Secondary row: avg growth delta, hidden-gems count.
- "Borderline" mini-list: the three just-missed candidates, clickable to their
  detail panel.
- Preset buttons: "Default", "Academic-heavy", "Growth-heavy" — one click, the
  bars move, the story tells itself.

## Demo script (30 seconds, no words needed)

Drag academic weight up → watch the underserved share drain out of the class.
Drag growth trajectory up → watch it come back. Say: "your policy, made
visible." That's the whole pitch.

## Done when

- Endpoint returns correct aggregates for a hand-computed fixture cohort (unit
  test with exact numbers; no AI involvement anywhere).
- Slider → panel round trip feels instant (<200 ms perceived).
- Bucket labels and the proxy disclaimer reviewed by the team.
- Committee-only (E4) verified.

## Risks / notes

With 16 synthetic candidates the percentages will be chunky (1 candidate =
5–6 %) — for the demo, consider growing the synthetic dataset to ~40 via
`generate_data.py` so the panel moves smoothly. That also makes ranking and
triage demos look more real.
