"""Central configuration for the backend.

Task FND-01. Model ids live here and nowhere else. Before this module they were
hard-coded at seven call sites, so when `claude-sonnet-4-20250514` was retired
every AI feature in the product failed at once and there was no single place to
fix it. Anything a deployment might need to change without touching code is read
from the environment with a working default.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── Models ─────────────────────────────────────────────────────────
# Judgement work (BARS rating, candidate scoring): strongest model available.
MODEL_JUDGE = os.getenv("MODEL_JUDGE", "claude-opus-5")
# Evidence extraction, drafting, redaction: cheaper, still strong on Kazakh.
MODEL_EXTRACT = os.getenv("MODEL_EXTRACT", "claude-sonnet-5")
# Conversational roleplay (teaching challenge / scenario lab counterpart).
MODEL_CHAT = os.getenv("MODEL_CHAT", "claude-sonnet-5")

# Never route Kazakh or code-switched text to a small model: low-resource
# languages degrade disproportionately on Haiku-class models.
MODEL_FOR_LOW_RESOURCE = MODEL_JUDGE

# ── Request shaping ────────────────────────────────────────────────
# Reasoning effort is optional. Left empty the parameter is not sent at all,
# which is the safe default until it is verified against a funded API key.
EFFORT_JUDGE = os.getenv("EFFORT_JUDGE", "")
EFFORT_EXTRACT = os.getenv("EFFORT_EXTRACT", "")

MAX_TOKENS_JSON = int(os.getenv("MAX_TOKENS_JSON", "4096"))
MAX_TOKENS_CHAT = int(os.getenv("MAX_TOKENS_CHAT", "400"))

# ── Reliability ────────────────────────────────────────────────────
# One cohort run must not open hundreds of sockets or exhaust the rate limit.
MAX_CONCURRENT_LLM_CALLS = int(os.getenv("MAX_CONCURRENT_LLM_CALLS", "4"))
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))

# ── Database ───────────────────────────────────────────────────────
# SQLite file next to the seed data by default. The path is absolute so the
# app finds the same database whatever directory uvicorn is started from.
_DEFAULT_DB = Path(__file__).resolve().parent / "data" / "invision.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_DEFAULT_DB.as_posix()}")

# ── Demo and debug ─────────────────────────────────────────────────
DEMO_MODE = os.getenv("DEMO_MODE", "1") == "1"

# ── Auth (FND-05) ──────────────────────────────────────────────────
# Signs access tokens. No default on purpose: the app refuses to start without
# it (backend/security.py). backend/.env.example ships a `dev-only-` secret
# that is accepted only with DEMO_MODE=1.
AUTH_SECRET = os.getenv("AUTH_SECRET", "")
AUTH_TOKEN_TTL_MINUTES = int(os.getenv("AUTH_TOKEN_TTL_MINUTES", "480"))

# Browser origins allowed to call the API, comma-separated.
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if origin.strip()
]
