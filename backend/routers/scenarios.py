"""Scenarios (INP-04): the applicant talks a real situation through with a conversation partner.

Replaces the teaching challenge. The applicant picks a scenario and a
language (English, Russian, Kazakh); the partner describes the situation,
raises two complications, then asks for a real example from the applicant's
life. On Finish, the applicant's replies are rated for the scenario's one
competency by the same pipeline as the essays (`backend.ledger.scenario`).

The result is observed in simulation and carries weight zero: it is shown to
the committee next to the written evidence and never changes the AI level, a
rank or a recommendation. The applicant does not see a level.

With a model key the partner answers live; without one it says the scripted
lines (demo mode), and the result says which it was.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable
from typing import Literal, TypeVar

import anthropic
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from backend import llm, scenarios, settings
from backend.db import candidates as candidate_store
from backend.db import feynman as store
from backend.db.tables import FeynmanStatus
from backend.ledger import scenario as scenario_rating
from backend.ledger.schema import CompetencyRating
from backend.routers.guards import ensure_candidate_access, require_role
from backend.security import ALL_ROLES, Role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])

T = TypeVar("T")

# Messages in a session, the partner's opening included: the opening, three
# replies and three follow-ups make 7; one spare reply is allowed.
MIN_REPLIES_TO_FINISH = 3
MAX_REPLIES = 5

# Nothing from a scenario reaches the AI level, a rank or a recommendation.
SIMULATION_WEIGHT = 0.0
SIMULATION_LABEL = "observed in simulation"
DEMO_MODEL = "demo-scripted"


# ── Request/Response models ────────────────────────────────────────


class ScenarioMode(BaseModel):
    live: bool
    reason: str | None = None


class StartRequest(BaseModel):
    candidate_id: str
    scenario_id: str
    language: scenarios.Language = "en"


class StartResponse(BaseModel):
    session_id: str
    scenario: dict
    language: scenarios.Language
    first_message: str
    live: bool


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    replies: int
    can_finish: bool
    must_finish: bool = False


class FinishResponse(BaseModel):
    session_id: str
    saved: bool = True


class ScenarioResultOut(BaseModel):
    """What the committee sees: the rating, the conversation, where it came from."""

    session_id: str
    candidate_id: str
    scenario: dict
    language: scenarios.Language
    competency: str
    rating: CompetencyRating
    messages: list[dict]
    source: Literal["live", "demo"]
    weight: float = SIMULATION_WEIGHT
    label: str = SIMULATION_LABEL


# ── Helpers ────────────────────────────────────────────────────────


def _scenario(scenario_id: str) -> dict:
    entry = scenarios.scenario(scenario_id)
    if entry is None:
        raise HTTPException(status_code=400, detail=f"Unknown scenario: {scenario_id}")
    return entry


def _mode() -> ScenarioMode:
    if llm.is_configured():
        return ScenarioMode(live=True)
    return ScenarioMode(live=False, reason="No model API key on this server: the conversation partner follows a script.")


def _own_session(session_id: str, user: dict) -> dict:
    """The session, if the caller started it. Someone else's is reported as
    missing, so session ids cannot be probed. Sync: reads the database."""
    session = store.get_session(session_id)
    if not session or session["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def _ensure_active(session: dict) -> None:
    if session["status"] != FeynmanStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This conversation is closed. Start a new one.")


def _replies(messages: list[dict]) -> int:
    return sum(1 for m in messages if m["role"] == "user")


def _no_attempts_left() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"You have used all {settings.FEYNMAN_MAX_ATTEMPTS} attempts at the scenarios.",
    )


async def _ask_model(call: Awaitable[T], action: str) -> T:
    """Await a model call; turn any failure into an HTTP error the browser can read.

    The underlying error is logged, not returned: it can carry request ids and
    account details.
    """
    try:
        return await call
    except llm.ModelUnavailable:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="The conversation partner is not available on this server.")
    except anthropic.RateLimitError:
        logger.warning("scenario %s: model rate limited", action)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The conversation partner is busy right now. Please wait a minute and try again.",
        )
    except Exception:
        logger.exception("scenario %s: model call failed", action)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="The conversation partner could not answer right now. Please try again.")


async def _partner_reply(session: dict, messages: list[dict]) -> str:
    """The partner's next line: the model when live, the script otherwise."""
    scenario_id, language = session["topic_id"], session["language"]
    if not llm.is_configured():
        return scenarios.scripted_reply(scenario_id, language, _replies(messages))
    # The opening is in the system prompt; the model's history starts with the applicant.
    return await _ask_model(
        llm.complete_chat(messages=messages[1:], system=scenarios.partner_system_prompt(scenario_id, language)), "chat"
    )


# ── Endpoints ──────────────────────────────────────────────────────


@router.get("")
def list_scenarios(_user: dict = Depends(require_role(*ALL_ROLES))):
    """The scenarios in every language, with the partner's name in each."""
    return {
        "languages": scenarios.LANGUAGES,
        "partner_label": scenarios.PARTNER_LABEL,
        "content_hash": scenarios.content_hash(),
        "scenarios": [scenarios.public(entry) for entry in scenarios.SCENARIOS],
    }


@router.get("/mode", response_model=ScenarioMode)
def scenario_mode(_user: dict = Depends(require_role(*ALL_ROLES))):
    """Whether the partner answers live, or follows the script (demo mode)."""
    return _mode()


@router.post("/start", response_model=StartResponse)
async def start(req: StartRequest, user: dict = Depends(require_role(Role.APPLICANT))):
    """Open a conversation. Each start uses one of `settings.FEYNMAN_MAX_ATTEMPTS`."""
    await run_in_threadpool(ensure_candidate_access, user, req.candidate_id)
    entry = _scenario(req.scenario_id)
    opening = scenarios.text(entry["id"], req.language)["opening"]
    session = await run_in_threadpool(
        store.create_session,
        user["applicant_id"],
        user["id"],
        entry["id"],
        [{"role": "assistant", "content": opening}],
        settings.FEYNMAN_MAX_ATTEMPTS,
        req.language,
    )
    if session is None:
        raise _no_attempts_left()
    return StartResponse(
        session_id=session["id"], scenario=scenarios.public(entry), language=req.language, first_message=opening, live=_mode().live
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, user: dict = Depends(require_role(Role.APPLICANT))):
    """Send a reply; get the partner's next line."""
    session = await run_in_threadpool(_own_session, req.session_id, user)
    _ensure_active(session)
    if _replies(session["messages"]) >= MAX_REPLIES:
        raise HTTPException(status_code=400, detail="This conversation is complete. Please finish it.")

    messages = session["messages"] + [{"role": "user", "content": req.message}]
    reply = await _partner_reply(session, messages)
    messages.append({"role": "assistant", "content": reply})

    # Nothing is stored until the reply is in, so a failed call leaves the
    # session as it was and the applicant can resend the same message.
    if not await run_in_threadpool(store.record_exchange, session["id"], session["exchange_count"], messages):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Another message was sent at the same time. Reload and try again.")

    replies = _replies(messages)
    return ChatResponse(reply=reply, replies=replies, can_finish=replies >= MIN_REPLIES_TO_FINISH, must_finish=replies >= MAX_REPLIES)


@router.post("/finish", response_model=FinishResponse)
async def finish(session_id: str, user: dict = Depends(require_role(Role.APPLICANT))):
    """Close the conversation and rate the replies. The applicant gets no level back."""
    session = await run_in_threadpool(_own_session, session_id, user)
    _ensure_active(session)
    if _replies(session["messages"]) < MIN_REPLIES_TO_FINISH:
        raise HTTPException(status_code=400, detail=f"Answer at least {MIN_REPLIES_TO_FINISH} times before finishing.")
    if not await run_in_threadpool(store.claim_for_scoring, session_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This conversation is already being scored.")

    competency = _scenario(session["topic_id"])["competency"]
    try:
        if llm.is_configured():
            rating = await _ask_model(
                scenario_rating.rate_live(session["messages"], competency, user["candidate_id"] or "", settings.MODEL_EXTRACT), "score"
            )
            source, model = "live", settings.MODEL_JUDGE
        else:
            rating = scenario_rating.rate_demo(session["messages"], competency)
            source, model = "demo", DEMO_MODEL
    except BaseException:
        # Model failure or a dropped request: reopen it so Finish can be retried.
        await run_in_threadpool(store.release_scoring, session_id)
        raise
    await run_in_threadpool(store.save_result, session_id, competency.value, rating.model_dump(mode="json"), source, model)
    return FinishResponse(session_id=session_id)


@router.get("/result/{candidate_id}", response_model=ScenarioResultOut | None)
def get_result(candidate_id: str, _user: dict = Depends(require_role(Role.COMMITTEE, Role.ADMIN))):
    """The latest finished scenario for a candidate. Committee and admin only: applicants see no level."""
    applicant_id = candidate_store.applicant_id_for(candidate_id)
    if applicant_id is None:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
    result = store.latest_result(applicant_id)
    if result is None:
        return None
    session = store.get_session(result["session_id"])
    entry = scenarios.scenario(session["topic_id"])
    return ScenarioResultOut(
        session_id=result["session_id"],
        candidate_id=candidate_id,
        scenario=scenarios.public(entry) if entry else {"id": session["topic_id"]},
        language=session["language"],
        competency=result["competency"],
        rating=CompetencyRating.model_validate(result["rating"]),
        messages=session["messages"],
        source=result["source"],
    )
