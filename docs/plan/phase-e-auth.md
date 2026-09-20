# Phase E — Auth Hardening

> Prerequisite: D5 (users live in the `users` table). Four small PRs.
> Current state being fixed: unsalted SHA-256 password "hashing" with a shared
> secret, homemade tokens with **no expiry**, in-memory users, and zero
> role enforcement on committee endpoints.

---

## E1 — Real password hashing (bcrypt) · S

**Why:** `sha256(secret + password)` is fast (billions/sec on a GPU) and
unsalted (identical passwords → identical hashes). bcrypt is deliberately slow
and salts automatically.

**New concept:** `passlib` with the bcrypt backend — the standard Python
password-hashing façade. One `CryptContext` object gives `hash()` and `verify()`.

**Files:** new `backend/security.py` (hashing + JWT live here, out of the
router); edit `backend/routers/auth.py`; add `passlib[bcrypt]` to requirements.

**Spec:**
- `pwd_context = CryptContext(schemes=["bcrypt"])`.
- `hash_password(p) -> str`, `verify_password(plain, hashed) -> bool`.
- Register uses `hash_password`; login uses `verify_password` (constant-time,
  no more comparing recomputed hashes).
- Re-seed the committee demo user with a bcrypt hash; the demo password itself
  moves to an env var (`COMMITTEE_DEMO_PASSWORD`) — no credentials in code.

**Done when:** two users with the same password have different stored hashes;
login works; old-format hashes are gone (dev DB is reseeded, nothing to migrate).

**Gotcha:** bcrypt silently truncates passwords at 72 bytes — fine here, but
know it exists. Keep `min_length` validation on the password field (raise it
from 4 to 8 while you're in there).

---

## E2 — Real JWT with expiry · S

**Why:** current tokens are `user_id:timestamp:truncated-hmac` with no
expiration — a leaked token works forever, and the 16-hex-char signature is
weak.

**New concept:** `PyJWT` — signed tokens with registered claims. `sub` (subject
= user id), `exp` (expiry), `iat` (issued at), plus a custom `role` claim.

**Files:** `backend/security.py`, `backend/routers/auth.py`; add `pyjwt` to
requirements.

**Spec:**
- `create_access_token(user_id, role)` → `jwt.encode({"sub": ..., "role": ...,
  "iat": now, "exp": now + settings.access_token_expire_minutes}, settings.auth_secret,
  algorithm="HS256")`. All times UTC.
- `get_current_user` dependency: decode with `jwt.decode(..., algorithms=["HS256"])`;
  `ExpiredSignatureError`/`InvalidTokenError` → return None (endpoints translate
  to 401); then load the user **from the DB** (a valid token for a deleted user
  must fail).
- `settings.auth_secret` is **required with no default** (A2) — the current
  baked-in `"invisionu-hackathon-secret-2026"` string dies in this PR.

**Done when:** `/me` works with a fresh token; a token forged with a different
secret → 401; a token with `exp` in the past → 401 (test by issuing with
-1 minute); tampering with one payload byte → 401.

**Gotchas:** return 401 (not 500) on every decode failure; don't log tokens;
frontend already stores the token client-side — keep the Bearer-header contract
unchanged so `useAuth.ts` keeps working. (Cookie-based sessions are a prod
upgrade — noted in production-readiness, not now.)

---

## E3 — Persistent users + candidate linking · S

**Why:** D5 moved storage; this PR finishes the loop — `link-candidate`
becomes an UPDATE, register enforces the unique email index (no more O(n) scan),
and login queries by email.

**Spec:** register → INSERT (catch unique-violation → 400 "email already
registered"); login → SELECT by email + `verify_password`; `/link-candidate` →
verify the candidate exists, then `UPDATE users SET candidate_id=...`. Also
validate email format (pydantic `EmailStr`; add `email-validator` dep).

**Done when:** users and links survive restart; duplicate registration → 400;
linking a nonexistent candidate → 404.

---

## E4 — Role-based access control · S

**Why:** committee-only endpoints (override, ranking, comparison, detection
results, cohort stats) are currently open to anyone — including, once the
public sandbox (Fool the Machine) ships, to complete strangers.

**New concept:** a dependency-of-a-dependency —
`require_committee(user = Depends(get_current_user))` raises 403 unless
`user.role == "committee"`; endpoints declare `Depends(require_committee)`.

**Endpoint policy table (agree with Rauan before implementing):**

| Endpoint group | Policy |
|---|---|
| `POST /api/candidates/` (apply), `GET /api/feynman/topics`, feynman start/chat/finish | applicant token **or** guest (Arman Live guest mode) |
| `GET /api/candidates/`, `/api/scoring/*`, `/api/analysis/ai-detection/*`, override, reweight, cohort stats, triage | **committee only** |
| `GET /api/candidates/{id}` | committee, or the applicant whose `candidate_id` matches |
| `/api/analysis/sandbox` (Fool the Machine) | public but rate-limited (see feature spec) |
| `/api/feynman/leaderboard` | public read-only |

**Done when:** applicant token on a committee endpoint → 403; committee token →
200; the frontend dashboard sends the token (small change in `api.ts`: attach
`Authorization` header from stored token to committee calls).

**Gotcha:** this is the PR most likely to break the frontend — coordinate: the
dashboard currently calls scoring endpoints with no auth header at all. Ship
backend-permissive first (warn-only log), flip to enforce after the frontend
attaches tokens.
