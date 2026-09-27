# Feature — Local Models 🔧 (Whisper, embeddings, optional Ollama fallback)

> The agreed division of labor: **Claude stays the brain (all judgment tasks);
> local models become the organs** — ears (Whisper), associative memory
> (embeddings), and an emergency backup brain-stem (Ollama, off by default).
> No local chat model in any judgment path: 7–9B quantized models are visibly
> worse at rubric JSON, persona consistency, and Kazakh — exactly our
> differentiators.
> Prerequisites: C (compose); A2/A3 (config + client seam). Independent of D/E.

---

## LM1 — Local Whisper transcription service · M

**Why:** the README lists "video analysis uses mock transcript by default" as a
known limitation, gated on a *paid* OpenAI key. `faster-whisper` (CTranslate2
runtime) runs on CPU, free, and transcription is a batch step — nobody waits
live, so CPU latency is fine. Bonus demo line: **"applicant voices never leave
our machine"** — a genuine privacy point for admissions data and on-prem-minded
universities.

**Architecture decision:** a **sidecar container**, not an in-process import —
keeps the ~1 GB model + ffmpeg out of the backend image and lets the service be
scheduled/scaled separately.

**Spec — `whisper-service/` (new top-level dir):**
- Tiny FastAPI app, one endpoint: `POST /transcribe` (multipart file) →
  `{text, language, duration_sec}`; `GET /healthz`.
- `faster-whisper` with `model_size` from env; ffmpeg in the image for audio
  extraction from video containers.
- Model choice table (pick via env, default `small`):

| Model | RAM (int8) | Speed (CPU) | RU quality | KZ quality |
|---|---|---|---|---|
| `base` | ~0.5 GB | fast | okay | poor |
| `small` | ~1 GB | ~1–2× realtime | good | fair |
| `medium` | ~2.5 GB | slow on CPU | very good | usable |

- Compose service `whisper` with a healthcheck; backend gets
  `settings.whisper_url`.
- Limits: max upload 100 MB; formats mp4/webm/m4a/mp3/wav; 413 otherwise.

**Backend integration (`video_analyzer.py`):** transcript source priority
becomes: (1) pasted `video_transcript`; (2) **uploaded file → whisper sidecar**
(new endpoint `POST /api/candidates/{id}/video` accepting the file, calling the
sidecar via async httpx, storing the transcript on the candidate); (3) mock,
with `is_mock=true` clearly surfaced. Delete the OpenAI-key branch once this
works — one fewer paid dependency.

**Done when:** uploading a phone-recorded RU clip through the UI yields a real
transcript feeding the existing Claude analysis; `is_mock` is false; the
whole flow works offline from Anthropic's perspective (only the analysis call
goes out).

---

## LM2 — Local embeddings: semantic voice-match + cross-applicant similarity · M

**Why (two concrete upgrades):**
1. The essay↔interview "voice match" is currently **Jaccard word overlap** —
   a paraphrased AI essay sails through because it shares meaning, not words.
   Embedding cosine similarity compares *meaning* and is multilingual out of
   the box.
2. **Cross-applicant essay clustering** — flag suspiciously similar essays
   *between different candidates* (shared ghostwriter / same ChatGPT prompt).
   Pairwise across a cohort is O(n²) — unaffordable via any API, trivial
   locally. **No other team will have this.**

**Model:** `intfloat/multilingual-e5-small` via `sentence-transformers`
(~120M params, CPU-fast, KZ/RU/EN covered). Upgrade path: `bge-m3` if quality
demands it. In-process in the backend is acceptable (one-time ~0.5 GB RAM); a
sidecar mirrors LM1 if image size becomes annoying — start in-process, simplest.

**Spec:**
- `backend/scoring/embeddings.py`: lazy-loaded singleton model;
  `embed(texts: list[str]) -> np.ndarray`; `cosine(a, b)`.
- **Voice match:** add `semantic_voice_similarity` to `StylometryMetrics`;
  compute in `compute_stylometry` when an interview exists; wire into
  `compute_statistical_score` with its own thresholds (calibrate on the
  synthetic dataset: score all 16, eyeball the spread, set flag threshold below
  the honest cluster). Keep Jaccard too — two weak signals beat one.
- **Similarity matrix:** `POST /api/analysis/essay-similarity` (committee-only):
  embed all essays, cosine all pairs, return pairs above `0.90` (tune!) with
  both candidate ids and the score; persist to an `essay_similarities` table
  (post-D). Dashboard: a warning chip on affected candidates + a detail list.
- Model files: bake into the image at build time or mount a volume — **no
  download at request time.**

**Done when:** a hand-made paraphrase pair scores high similarity while two
unrelated essays score low (fixture test with pinned expected ranges); the
16-candidate matrix computes in <5 s CPU; dashboard shows a flag for a planted
duplicate pair in the synthetic data.

**Prod note:** at real-cohort scale, store vectors in Postgres with **pgvector**
instead of recomputing — the migration is additive (one extension, one column).

---

## LM3 — Ollama fallback (optional, off by default) · S/M

**Purpose, narrowly:** *offline/degraded demo insurance and an "on-prem
capable" slide* — never a quality path. If venue Wi-Fi or the Anthropic API
dies mid-demo, flip an env var and the Feynman chat limps along locally.

**Spec:**
- The seam goes in `backend/llm.py`, and `complete_chat(messages, system, model)` is already
  shaped like it — give it two implementations, Anthropic (default) and Ollama
  (`qwen2.5:7b-instruct` via Ollama's HTTP API), selected by a new `settings.AI_PROVIDER`.
  **Only `complete_chat` gets the seam**; `complete_json` stays Anthropic-only, because a local
  model cannot honor the structured-output schema the scorer, detector and letters depend on —
  and we want those to fail loudly rather than silently degrade judgment quality. That split
  falls out of the existing two-function API for free.
- Compose: `ollama` service under a **profile** (`--profile fallback`) so it
  never runs by default; model pulled at image build or documented one-time
  `ollama pull`.
- UI: when in fallback mode, show a small "degraded mode" banner — honesty on
  stage beats a silent quality drop.
- Expectations, documented where the team sees them: 7B Q4 on CPU ≈ 5–15
  tok/s → 10–20 s per Arman reply; JSON side-channel likely unreliable → in
  fallback mode skip the understanding meter (frontend already degrades, AL1).

**Done when:** with Wi-Fi off, `AI_PROVIDER=ollama` + profile up yields a
complete (slow) guest session; with the flag off, Ollama is never contacted.

**Explicitly rejected (and why, for the record):** replacing Claude for
scoring/detection/Feynman-eval with local models — quality cliff on rubric
JSON and Kazakh, latency unacceptable for voice, and the eng time belongs in
the features above. Revisit only if a customer demands full on-prem, at which
point it's a priced project, not a hackathon stretch.
