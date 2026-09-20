# Feature — No Dead Ends 🥈 (rejection growth letters)

> Every candidate scored "needs attention" gets a personalized, evidence-based
> growth letter generated from *their own extracted signals*: what was strong,
> what was thin, and three concrete actions before reapplying.
> The pitch line: **"Every other admissions system says no and goes silent.
> Ours says no and hands you a map."** For a scholarship program aimed at
> overlooked kids — and for inDrive's fairness brand — this is the emotional
> closer of the demo.
> Prerequisites: D (letters persisted; scores queryable), A3 (central client),
> E4 (committee gate on generation/approval).

---

## Design principles (agree before building)

1. **Human-in-the-loop, consistent with the project's ethos:** the letter is
   generated as a **draft**; a committee member reads and approves it before an
   applicant can see it. `growth_letters.status: draft → approved`.
2. **Evidence-based, not generic:** the prompt receives the candidate's
   extracted signals + dimension scores with `concerns` + Feynman results, and
   is instructed to reference *specific* items ("your growth delta was in the
   top 30%, but your essay never mentions the volunteer project listed in your
   activities"). Generic encouragement is a failure mode — say so in the prompt.
3. **Language-matched:** detect the essay language (`detect_language` already
   exists) and write the letter in it.
4. **PII-safe:** generation uses the anonymized candidate (existing
   `anonymize_candidate`); the letter template addresses "you", so no name is
   needed in the prompt at all.

## Backend spec · S/M

**New module:** `backend/scoring/growth_letter.py`

- `async generate_growth_letter(candidate, score, feynman_score | None,
  detection | None) -> GrowthLetter`.
- Prompt inputs: `signals_to_context(extract_signals(candidate))` (already
  exists — reuse!), dimension scores with explanations + concerns, Feynman
  summary if present.
- Output structure (structured outputs again — schema-enforced):
  `{strengths: [2-3 items with evidence], gaps: [2-3 items with evidence],
  plan_90_days: [3 concrete actions], reapply_note: str, language: str}`.
  Store both the structured JSON and a rendered text version.
- Tone constraints in the prompt: warm, specific, teen-appropriate, no
  platitudes, never mention scores/numbers directly, never promise admission.
- Model: the default judgment model (this is quality-sensitive writing; don't
  route to Haiku).

**Endpoints:**

| Endpoint | Auth | Behavior |
|---|---|---|
| `POST /api/candidates/{id}/growth-letter` | committee | generate (or regenerate) draft; upsert into `growth_letters` |
| `PUT /api/candidates/{id}/growth-letter/approve` | committee | mark approved (optionally with edited text in body) |
| `GET /api/candidates/{id}/growth-letter` | committee, or the linked applicant **only if approved** | fetch |

**Cost note:** one call per rejected candidate, cached forever in the DB.
For a 500-candidate cohort with ~40% rejections that's ~200 calls — this is a
[Message Batches API](production-readiness.md#cost-self-sustainability)
candidate (50% off, overnight) at pilot scale.

## Frontend spec · S

- Dashboard, candidate detail panel: for `needs attention` candidates, a
  "Generate growth letter" button → modal with the draft (strengths / gaps /
  plan sections), inline-editable, Approve button, copy-to-clipboard.
- Applicant portal (post-E3 linking): if a letter is approved for your
  candidate_id, show it on your status page.

## Demo script

Open the weakest-scored synthetic candidate → generate live (or pre-generated
the night before — safer) → read one specific line aloud. Close with the pitch
sentence. 45 seconds, maximal heart.

## Done when

- Letter generation works with mocked Claude in tests (fixture letter);
  structure validates; empty Feynman/detection handled.
- Draft/approve flow enforced (unapproved letters invisible to applicants — test it).
- Letters survive restart; regeneration overwrites the draft, never an approved letter without an explicit flag.
- One real generated letter per language reviewed by the team for tone before demo.

## Risks

Hallucinated specifics → mitigated the same way scoring is: the prompt only
receives extracted signals, and instructs "reference only the facts above."
Sensitive tone for minors → that's what the human approval step is for.
