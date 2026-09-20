# Feature — Arman Live 🥇 (the killer feature)

> Turn the Feynman challenge from a text chat the presenter demos into a
> **voice-driven, emotionally visible experience the judges play themselves.**
> Prerequisites: F1 (async Feynman — hard requirement for concurrent sessions),
> A2 (LAN/CORS config), D5 (persisted sessions/scores — required from AL3 on).
> Build in stages; each stage is independently demoable.

**Why this wins:** judges reward participation and emotion. Nobody else will
have "teach an AI child, out loud, and watch it understand." It *demonstrates*
the project thesis — "the best way to find a leader is to watch them teach" —
instead of claiming it.

---

## AL1 — Arman's visible state: the understanding meter · S/M

**What:** every Arman reply carries a machine-readable emotional state; the UI
renders an animated face + an "understanding" bar that moves as you teach.

**Backend spec (`feynman.py`):**
- Change the chat call to use **structured outputs** so each turn returns
  `{"reply": str, "mood": "confused"|"thinking"|"excited"|"happy",
  "understanding": int 0-100}` — schema-enforced (via
  `output_config={"format": {"type": "json_schema", "schema": ...}}`), so no
  regex stripping and no parse crashes on stage.
  - Prompt addition to `STUDENT_SYSTEM_PROMPT`: explain the three fields;
    `understanding` = "how well do you understand the topic *so far*, as this
    10-year-old"; instruct that the misunderstanding moment should *drop* it.
  - Alternative (only if structured outputs interferes with streaming in AL6):
    append a `<state>{"mood":...,"understanding":...}</state>` tag line and
    strip it server-side; on parse failure default to
    `{"mood":"thinking","understanding":null}` — **never fail the request over
    the side-channel.**
- Extend `ChatResponse` with `mood` and `understanding` (optional fields —
  frontend degrades gracefully).
- Persist per-turn state into the session's `messages` JSONB (D5), e.g. store
  each assistant message as `{role, content, mood, understanding}` — this array
  is the **understanding trace**.
- On `/finish`, copy the trace into `feynman_scores.understanding_trace` and
  include it in the response.

**Frontend spec (`teach/page.tsx`):**
- Arman avatar with 4 expressions (designer task for Arman-the-human 🙂 — 4 PNGs
  or a simple CSS face); animated progress bar for `understanding`; small
  bounce/transition when it jumps.
- Results screen: line chart of understanding-per-exchange with the biggest
  positive delta annotated — *"this is the moment your analogy landed."*
  (Chart: tiny inline SVG or a ~2 KB sparkline component; no chart library needed.)

**Done when:** a full session shows live mood/meter; the trace renders on the
results page; a malformed model response degrades to neutral state instead of
erroring; tests cover the parser with good/missing/garbage fixtures.

**Cost:** ~20 extra output tokens per turn. Negligible.

---

## AL2 — Voice in, voice out · M (frontend only, $0)

**What:** the teacher *speaks* to Arman; Arman *speaks back*.

**Spec — speech-to-text (browser `SpeechRecognition`):**
- Feature-detect `window.SpeechRecognition || window.webkitSpeechRecognition`;
  if absent, hide the mic button (text input always remains).
- **Push-to-talk**, not continuous: hold/tap mic → start recognition with
  `interimResults: true` (show live gray text) → on release/final, put the
  transcript into the input box for confirmation → user hits send (or
  auto-send after a 1s pause — make it a toggle).
- Language selector: `ru-RU`, `en-US`, `kk-KZ` (mark Kazakh "experimental" —
  Chrome support is inconsistent; **test on real devices early**, and fall back
  to text gracefully).
- Reality check: works in Chrome desktop/Android; iOS Safari support is
  limited — the judge-mode page must detect and fall back to typing without
  looking broken.

**Spec — text-to-speech (`speechSynthesis`):**
- Speak Arman's `reply` on arrival; pick a voice matching the session language
  from `getVoices()`; nudge `pitch: 1.3, rate: 1.05` for a kid-ish voice.
- Mute toggle (default **on** sound for the demo, off for judge mode in a loud
  hall — decide at rehearsal); stop speech when the user starts talking.
- Kazakh TTS voices are rare on most OSes — if no `kk` voice, show text only
  (and note that local Whisper, in [feature-local-models.md](feature-local-models.md),
  is the future path for Kazakh STT).

**Done when:** a full teaching session can be completed hands-on-keyboard-free
in Russian and English on Chrome desktop + one Android phone; every failure
mode falls back to the text UI.

**Gotchas:** browser STT requires HTTPS *or* localhost — for LAN demo either
run the frontend via `next dev --experimental-https`, use a tunnel, or accept
that phones use text input while the presenter laptop (localhost) uses voice.
Decide this at rehearsal, not on stage. (This is a genuine constraint — plan
for it.)

---

## AL3 — Guest sessions (judge mode backend) · M

**What:** anyone with the link can teach Arman without being a candidate.

**Backend spec:**
- `POST /api/feynman/start` accepts `{mode: "guest", nickname: str(1..20),
  topic_id}` — no `candidate_id`. Session row gets `candidate_id = NULL,
  guest_name = nickname`.
- Guest limits (protect the budget): `MAX_EXCHANGES = 5` for guests (8 for
  candidates); guest replies `max_tokens` stays 200; **rate limiting** via
  `slowapi` — e.g. 3 sessions/hour/IP on `/start`, 30 messages/hour/IP on
  `/chat`. Add `slowapi` to requirements; wire its middleware in `main.py`.
- A `DEMO_KILL_SWITCH` env flag (A2 settings) that disables guest starts
  instantly if the budget burns too fast.
- Profanity/PII care: nicknames are displayed on a projector — cap length,
  strip non-alphanumerics, and keep a tiny blocklist. Don't overbuild.

**Frontend spec:** `/teach?guest=1` (or `/play`) — nickname prompt → topic pick
→ same chat UI (voice included) → score screen with "you beat N% of players".
Mobile-first layout: this page is *the* phone experience.

**Done when:** two phones + the laptop can run three simultaneous sessions with
no cross-talk (this is what F1 bought you); a 4th rapid-fire session from the
same IP is rate-limited with a friendly message.

---

## AL4 — Leaderboard + QR · S/M

**Backend spec:**
- `GET /api/feynman/leaderboard?limit=20` → best score per person
  (`guest_name` or candidate name — candidates opt-in only, guests always
  shown), fields: `rank, name, topic_id, overall_score, clarity, quiz_transfer_score,
  created_at`. Public, cached for 5s in-process (cheap), reads `feynman_scores` (D).

**Frontend spec:**
- `/leaderboard` — projector page: big type, top-10 table, auto-refresh
  (poll every 5s; SSE is a later nicety), subtle highlight animation when a new
  entry lands, and the **QR code** (generate with the `qrcode` npm package from
  `settings`-driven public URL) pinned in a corner with "Teach Arman → get ranked".

**Done when:** finishing a guest session on a phone puts the nickname on the
projector within 5s; the QR resolves on a phone that's on the venue Wi-Fi.

**Network reality (rehearse this):** phones must reach the backend. Options in
order of reliability: (1) your own travel router / phone hotspot with laptop +
phones on it, frontend served on LAN IP, `cors_origins` + `NEXT_PUBLIC_API_URL`
set accordingly (A2 makes this a `.env` edit); (2) a tunnel (cloudflared/ngrok
free tier) if venue Wi-Fi isolates clients — also solves AL2's HTTPS-for-mic
requirement. Test both at the venue before your slot.

---

## AL5 — The "moment it clicked" results screen · S

Ties AL1's trace + AL3's guest flow into the shareable artifact:
score card (4 dimensions + quiz transfer), the understanding sparkline with the
annotated jump, Arman's one-line summary, and a "play again" button. This
screen is the screenshot that goes in the deck and the article.

---

## AL6 — Streaming replies (stretch, prod-quality voice) · M

**Why:** waiting 3–5s for a full reply feels slow in voice mode. Streaming cuts
time-to-first-word to <1s and lets TTS start on the first sentence.

**Spec:** new `POST /api/feynman/chat/stream` returning **SSE**
(`text/event-stream`): backend uses `client.messages.stream(...)` (async SDK)
and forwards text deltas as SSE events; final event carries the state
side-channel + message_count bookkeeping. Frontend consumes with
`EventSource`/fetch-reader, renders tokens as they arrive, and feeds completed
sentences to `speechSynthesis`. If AL1 used structured outputs, this endpoint
uses the `<state>` tag alternative (tags stream naturally; JSON doesn't) — the
AL1 spec anticipates this.

**Done when:** first spoken word within ~1s of send; non-streaming endpoint
remains as fallback.

---

## Cost & risk controls (applies to all stages)

- **Prompt caching:** the Feynman conversation resends the whole history every
  turn — put a `cache_control: {"type": "ephemeral"}` breakpoint on the last
  message block each turn so prior turns hit the cache (reads ≈ 0.1× input
  price). Note the minimum cacheable prefix (~2–4K tokens depending on model):
  early turns won't cache — that's fine, the win is in long sessions. Verify
  with `usage.cache_read_input_tokens` in logs.
- **Model routing:** Arman's persona is a small-model task — `claude-haiku-4-5`
  ($1/$5 per MTok) is likely enough and is fastest (matters for voice); keep the
  session **evaluation** on the stronger default model. This is exactly why A2
  has `anthropic_model_chat`. A/B it: run 3 sessions on each, compare character
  consistency before committing.
- **Kill switch + rate limits** (AL3) are non-negotiable before publishing any
  public URL.
- Every prompt change lands with updated parser fixtures (B1) — the demo dies
  on parse errors, not on bad prose.
