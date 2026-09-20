# Demo-Day Playbook 🏁

> The unglamorous 10% that decides whether the other 90% is ever seen.
> Owner: whole team. Rehearse twice: T-3 days (full run) and T-1 day (at the
> venue if possible).

---

## T-7 days — freeze & harden

- [ ] Feature freeze for anything touching the demo path; only fixes land.
- [ ] Grow the synthetic dataset to ~40 candidates (`generate_data.py`) so
      rankings, triage, and the fairness panel look alive.
- [ ] Golden-set run (production-readiness § LLM quality ops) after the last
      prompt change; eyeball every Arman persona reply for character breaks.
- [ ] Full `docker compose up` from scratch on a teammate's clean machine.

## T-2 days — pre-compute everything

- [ ] Batch-score **all** candidates (baseline + AI) into the DB — the dashboard
      must never wait on a live scoring call during the pitch. (Batches API at
      50% off if budget matters.)
- [ ] Generate + approve growth letters for the 2 candidates used in the pitch.
- [ ] Run AI detection for all candidates; run essay-similarity; verify the
      planted duplicate pair flags.
- [ ] Record the **backup video** of the entire happy-path demo (screen capture
      with narration). If everything burns, you present the video.
- [ ] `pg_dump` the demo database; store the dump in the repo's release/drive.
      Restoring it is the 60-second recovery from *any* data weirdness.

## T-1 day — venue & network drill

- [ ] Decide the network topology and **test it in the room**:
      Plan A: travel router / phone hotspot; laptop + phones on it; frontend on
      LAN IP; `.env`: `cors_origins` + `NEXT_PUBLIC_API_URL` set to LAN address.
      Plan B: cloudflared/ngrok tunnel (also gives HTTPS → phone mics work for
      voice). Plan C: presenter-laptop-only demo (localhost voice works), QR
      section replaced by inviting one judge to the laptop.
- [ ] Verify browser mic permission + TTS voices **on the actual demo laptop**
      and on two team phones (RU + EN).
- [ ] Failure drills, actually performed:
      1. Kill Wi-Fi mid-chat → flip `AI_PROVIDER=ollama` (if LM3 shipped) or
         switch to the backup video segment. Time it.
      2. Kill the backend process → restart; confirm state (scores, leaderboard)
         survives (that's Phase D paying off). Time it: target <60s.
      3. Anthropic 429/outage → `DEMO_KILL_SWITCH` off guest mode, presenter
         continues with pre-scored dashboard data.
- [ ] Charge everything; bring the HDMI adapter; projector-test the leaderboard
      page (big type readable from the back row?).

## The pitch (7 minutes, roles assigned)

| Min | Beat | Driver |
|---|---|---|
| 0:00 | Problem + the village-kid candidate the baseline rejects | speaker |
| 0:30 | Trajectory + Feynman thesis; **live Arman Live session, by voice** — understanding meter visible | speaker teaches, laptop driver watches state |
| 3:00 | Fool the Machine — invite a judge's text, stats mode live | speaker + judge |
| 4:30 | Fairness sandbox slider moment + triage toggle | laptop driver |
| 5:30 | No Dead Ends letter, read one specific line | speaker |
| 6:15 | **The one number** + QR to the leaderboard ("play while we take questions") | both |

- The **one number** (compute at T-2 from the scored cohort): "rule-based
  screening alone would reject X of our top-10; the pipeline recovers them."
- Q&A landmines, answers ready: "AI detectors don't work" (→ 40/60 blend +
  human decision + show the sandbox), "bias in the LLM" (→ PII anonymization,
  evidence-quote requirement, override + audit panel), "cost" (→ routing table +
  caching + batch: cents per candidate, number ready), "why not fine-tune/local"
  (→ the local-models division-of-labor story).

## During judging (after your slot)

- Leaderboard stays on the projector; one teammate babysits the backend logs
  (`usage_log` + error stream) and the kill switch.
- If judges play: greet each leaderboard entry out loud — the attention is the point.

## T+1 — pilot follow-through

- Capture judge questions verbatim (they are customer discovery).
- Deploy the pilot stack on free-tier infra (production-readiness § infra map)
  while the code is fresh; send the link + one-pager to the inDrive contact
  within 48 hours — momentum is the whole game.
