"""Central configuration for the backend.

Task FND-01. Model ids live here and nowhere else. Before this module they were
hard-coded at seven call sites, so when `claude-sonnet-4-20250514` was retired
every AI feature in the product failed at once and there was no single place to
fix it. Anything a deployment might need to change without touching code is read
from the environment with a working default.
"""

from __future__ import annotations

import os

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

# ── Demo and debug ─────────────────────────────────────────────────
DEMO_MODE = os.getenv("DEMO_MODE", "1") == "1"
