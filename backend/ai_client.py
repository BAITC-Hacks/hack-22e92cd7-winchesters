"""Central Anthropic client and model configuration.

Single choke point for every Claude call in the backend:
- one place to construct the client (sync now; async variant ready for Phase F)
- one place to name models, overridable via env without code changes

Model routing:
    MODEL       -- judgment tasks (scoring, detection, evaluation, letters)
    CHAT_MODEL  -- persona tasks (Arman chat/quiz); falls back to MODEL

Note: Sonnet 5 runs adaptive thinking by default when `thinking` is omitted,
and `max_tokens` covers thinking + text combined. Persona calls with small
token budgets must pass `thinking={"type": "disabled"}` (see feynman.py);
judgment calls leave adaptive thinking on with a raised max_tokens.
"""

from __future__ import annotations

import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "claude-sonnet-5"

MODEL = os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)
CHAT_MODEL = os.getenv("ANTHROPIC_MODEL_CHAT") or MODEL

_client: anthropic.Anthropic | None = None
_async_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def get_async_client() -> anthropic.AsyncAnthropic:
    global _async_client
    if _async_client is None:
        _async_client = anthropic.AsyncAnthropic()
    return _async_client


def text_of(message: anthropic.types.Message) -> str:
    """First text block of a response.

    With adaptive thinking enabled, content may start with a thinking block —
    `message.content[0].text` is not safe.
    """
    for block in message.content:
        if block.type == "text":
            return block.text
    raise ValueError(f"No text block in response (stop_reason={message.stop_reason})")
