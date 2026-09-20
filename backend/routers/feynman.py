"""Feynman Reversal AI — Peer-to-AI Teaching evaluation.

The candidate teaches a concept to an AI agent prompted as a curious 10-year-old.
After the session, a separate AI scorer evaluates teaching quality and the
"student" takes a mini-quiz to measure knowledge transfer.
"""

from __future__ import annotations

import json
import os
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.ai_client import CHAT_MODEL, MODEL, get_client, text_of

router = APIRouter(prefix="/api/feynman", tags=["feynman"])

# Persona replies are short; adaptive thinking would eat the small max_tokens
# budget, so it is explicitly disabled on chat/quiz calls.
_NO_THINKING = {"type": "disabled"}


# ── Topics (generic, school-level) ─────────────────────────────────

TOPICS = [
    {
        "id": "seasons",
        "title": "Why We Have Seasons",
        "description": "Explain why summer is hot and winter is cold.",
    },
    {
        "id": "rain",
        "title": "How Rain Works",
        "description": "Explain where rain comes from and why it falls from the sky.",
    },
    {
        "id": "gravity",
        "title": "Why Things Fall Down",
        "description": "Explain why when you drop something, it falls to the ground.",
    },
    {
        "id": "cooking",
        "title": "Why We Cook Food",
        "description": "Explain why we cook food instead of eating everything raw.",
    },
    {
        "id": "money",
        "title": "Why Money Exists",
        "description": "Explain why people use money instead of trading things directly.",
    },
    {
        "id": "sleep",
        "title": "Why We Need Sleep",
        "description": "Explain why people and animals need to sleep every night.",
    },
    {
        "id": "teamwork",
        "title": "Why Teamwork Matters",
        "description": "Explain why working together helps people achieve more than working alone.",
    },
    {
        "id": "recycling",
        "title": "Why We Recycle",
        "description": "Explain why it's important to recycle things instead of throwing them away.",
    },
]

# ── In-memory session store ────────────────────────────────────────

_sessions: dict[str, dict] = {}

STUDENT_SYSTEM_PROMPT = """You are a curious, slightly confused 10-year-old child named Arman. You are eager to learn but you don't know any big words or complex concepts.

Rules for your behavior:
- You speak simply, like a real 10-year-old (short sentences, simple words)
- You ask "why?" and "what does that mean?" a lot
- If the teacher uses a big or complicated word, you say you don't understand and ask them to explain it simpler
- You sometimes make wrong guesses about things (that's okay, you're learning!)
- You get excited when you understand something ("Oh! So it's like when...")
- You try to relate things to your own life (school, games, food, friends)
- You are NOT pretending to be confused — you genuinely don't know these topics
- Keep your responses short (2-4 sentences max)
- You speak in the same language as the teacher (if they speak Kazakh, respond in Kazakh; Russian → Russian; English → English)
- IMPORTANT: After the teacher's 2nd or 3rd message, intentionally misunderstand ONE thing they said. Make a wrong conclusion based on their explanation. For example if they explain gravity, say "Oh! So heavier things fall faster than light things?" This tests their patience and ability to correct you kindly.
- NEVER break character. You are Arman, a 10-year-old.

The teacher is going to explain: {topic_description}

Start by saying hi and asking the teacher what they want to teach you today. Be excited but a little confused about the topic name."""

QUIZ_SYSTEM_PROMPT = """You are the same 10-year-old child (Arman) who just finished a teaching session about: {topic_description}

Based on ONLY what the teacher explained to you in the conversation (not your own knowledge), answer these 3 questions. Answer like a 10-year-old would — simple language, maybe not perfect, but showing whether you actually understood.

If the teacher didn't explain something well enough for you to answer, say "I don't think they explained that part" or "I'm not sure, they didn't really tell me about that."

Questions:
1. {q1}
2. {q2}
3. {q3}

Respond in JSON format:
{{
  "answers": [
    {{"question": 1, "answer": "<your answer>", "confident": true/false}},
    {{"question": 2, "answer": "<your answer>", "confident": true/false}},
    {{"question": 3, "answer": "<your answer>", "confident": true/false}}
  ]
}}
Return ONLY valid JSON."""

QUIZ_QUESTIONS: dict[str, list[str]] = {
    "seasons": [
        "Why is it hot in summer?",
        "Does the whole world have summer at the same time?",
        "Why are days longer in summer than in winter?",
    ],
    "rain": [
        "Where does rain come from?",
        "Why do clouds sometimes make rain and sometimes don't?",
        "What happens to rain after it falls on the ground?",
    ],
    "gravity": [
        "Why does a ball come back down when you throw it up?",
        "If you drop a feather and a rock, which hits the ground first and why?",
        "Why don't we float away into space?",
    ],
    "cooking": [
        "Why can't we eat raw chicken?",
        "What does heat do to food?",
        "Is all raw food bad for you?",
    ],
    "money": [
        "What did people do before money existed?",
        "Why can't we just trade things instead of using money?",
        "Why is a piece of paper (money) worth something?",
    ],
    "sleep": [
        "What happens to your body when you sleep?",
        "Why do you feel bad when you don't sleep enough?",
        "Do animals need sleep too?",
    ],
    "teamwork": [
        "Can you give an example of when teamwork is better than working alone?",
        "What happens when one person in a team doesn't do their part?",
        "Is it always better to work in a team?",
    ],
    "recycling": [
        "What happens to trash that isn't recycled?",
        "Can everything be recycled?",
        "Why should kids care about recycling?",
    ],
}

SCORER_PROMPT = """You are an expert evaluator for a university admissions process. You are reviewing a teaching session where a candidate (age 16-18) taught a concept to a 10-year-old AI student.

Topic: {topic_title} — {topic_description}

Here is the full conversation:
{conversation}

Here are the quiz results (how well the 10-year-old understood after being taught):
{quiz_results}

Evaluate the candidate's teaching ability across these 4 dimensions. Score each 0-100:

1. **Clarity** — Did they break down complex ideas into simple, understandable parts? Did they avoid jargon or explain it when used?
2. **Patience** — How did they handle confusion or wrong guesses? Did they get frustrated or adapt their explanation?
3. **Empathy** — Did they meet the student at their level? Did they use examples the student could relate to?
4. **Adaptability** — Did they change their approach when the student didn't understand? Did they try different analogies or methods?

Also provide:
- **quiz_transfer_score** (0-100): How well did the student actually learn? Based on quiz answers.
- **overall_score** (0-100): Weighted combination reflecting overall teaching quality.
- **summary**: 2-3 sentence assessment of the candidate as a teacher/communicator.

Respond in JSON:
{{
  "clarity": <0-100>,
  "patience": <0-100>,
  "empathy": <0-100>,
  "adaptability": <0-100>,
  "quiz_transfer_score": <0-100>,
  "overall_score": <0-100>,
  "summary": "<assessment>"
}}
Return ONLY valid JSON."""


# ── Request/Response models ────────────────────────────────────────


class StartSessionRequest(BaseModel):
    candidate_id: str
    topic_id: str


class StartSessionResponse(BaseModel):
    session_id: str
    topic: dict
    first_message: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    message_count: int
    can_finish: bool  # True after 4+ exchanges
    must_finish: bool = False  # True at 8 exchanges (hard limit)
    remaining: int = 0  # exchanges remaining before hard limit


class QuizAnswer(BaseModel):
    question: str
    answer: str
    confident: bool = False


class FeynmanScore(BaseModel):
    session_id: str
    candidate_id: str
    topic_id: str
    clarity: float = 0
    patience: float = 0
    empathy: float = 0
    adaptability: float = 0
    quiz_transfer_score: float = 0
    overall_score: float = 0
    summary: str = ""
    message_count: int = 0
    quiz_answers: list[QuizAnswer] = []


# ── Score cache ────────────────────────────────────────────────────

_score_cache: dict[str, FeynmanScore] = {}


# ── Endpoints ──────────────────────────────────────────────────────


@router.get("/topics")
def list_topics():
    """List available teaching topics."""
    return TOPICS


@router.post("/start", response_model=StartSessionResponse)
def start_session(req: StartSessionRequest):
    """Start a new teaching session. Returns the AI student's first message."""
    topic = next((t for t in TOPICS if t["id"] == req.topic_id), None)
    if not topic:
        raise HTTPException(status_code=400, detail=f"Unknown topic: {req.topic_id}")

    session_id = str(uuid.uuid4())[:8]
    system = STUDENT_SYSTEM_PROMPT.format(topic_description=topic["description"])

    client = get_client()
    response = client.messages.create(
        model=CHAT_MODEL,
        max_tokens=200,
        thinking=_NO_THINKING,
        system=system,
        messages=[{"role": "user", "content": f"Hi Arman! Today I'm going to teach you about {topic['title']}."}],
    )

    first_msg = text_of(response)

    _sessions[session_id] = {
        "candidate_id": req.candidate_id,
        "topic_id": req.topic_id,
        "topic": topic,
        "system": system,
        "messages": [
            {"role": "user", "content": f"Hi Arman! Today I'm going to teach you about {topic['title']}."},
            {"role": "assistant", "content": first_msg},
        ],
        "exchange_count": 1,
    }

    return StartSessionResponse(
        session_id=session_id,
        topic=topic,
        first_message=first_msg,
    )


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Send a message in the teaching session. Returns the AI student's reply."""
    MAX_EXCHANGES = 8

    session = _sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session["exchange_count"] >= MAX_EXCHANGES:
        raise HTTPException(status_code=400, detail="Session has reached the maximum number of exchanges. Please finish the session.")

    session["messages"].append({"role": "user", "content": req.message})

    client = get_client()
    response = client.messages.create(
        model=CHAT_MODEL,
        max_tokens=200,
        thinking=_NO_THINKING,
        system=session["system"],
        messages=session["messages"],
    )

    reply = text_of(response)
    session["messages"].append({"role": "assistant", "content": reply})
    session["exchange_count"] += 1

    count = session["exchange_count"]
    remaining = MAX_EXCHANGES - count

    return ChatResponse(
        reply=reply,
        message_count=count,
        can_finish=count >= 4,
        must_finish=count >= MAX_EXCHANGES,
        remaining=remaining,
    )


@router.post("/finish", response_model=FeynmanScore)
def finish_session(session_id: str):
    """End the session, run the quiz, and score the teaching performance."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    topic = session["topic"]
    topic_id = session["topic_id"]
    client = get_client()

    # ── Step 1: Quiz the AI student ────────────────────────────────
    questions = QUIZ_QUESTIONS.get(topic_id, QUIZ_QUESTIONS["gravity"])

    quiz_system = QUIZ_SYSTEM_PROMPT.format(
        topic_description=topic["description"],
        q1=questions[0],
        q2=questions[1],
        q3=questions[2],
    )

    quiz_response = client.messages.create(
        model=CHAT_MODEL,
        max_tokens=500,
        thinking=_NO_THINKING,
        system=quiz_system,
        messages=session["messages"] + [
            {"role": "user", "content": "Okay Arman, quiz time! Answer the questions based on what I taught you."},
        ],
    )

    quiz_text = text_of(quiz_response)

    # Parse quiz answers for transparency
    parsed_quiz: list[QuizAnswer] = []
    try:
        cleaned_quiz = quiz_text.strip()
        if cleaned_quiz.startswith("```"):
            cleaned_quiz = cleaned_quiz.split("\n", 1)[1]
        if cleaned_quiz.endswith("```"):
            cleaned_quiz = cleaned_quiz.rsplit("```", 1)[0]
        quiz_data = json.loads(cleaned_quiz.strip())
        for ans in quiz_data.get("answers", []):
            q_idx = int(ans.get("question", 1)) - 1
            parsed_quiz.append(QuizAnswer(
                question=questions[q_idx] if 0 <= q_idx < len(questions) else f"Question {q_idx+1}",
                answer=ans.get("answer", ""),
                confident=ans.get("confident", False),
            ))
    except Exception:
        # If parsing fails, include raw quiz text
        for i, q in enumerate(questions):
            parsed_quiz.append(QuizAnswer(question=q, answer="(could not parse response)", confident=False))

    # ── Step 2: Score the conversation ─────────────────────────────
    conversation_text = "\n".join(
        f"{'Teacher' if m['role'] == 'user' else 'Arman (student)'}: {m['content']}"
        for m in session["messages"]
    )

    scorer_prompt = SCORER_PROMPT.format(
        topic_title=topic["title"],
        topic_description=topic["description"],
        conversation=conversation_text,
        quiz_results=quiz_text,
    )

    # Judgment call: adaptive thinking stays on; max_tokens covers it + the JSON
    score_response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": scorer_prompt}],
    )

    raw = text_of(score_response).strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]

    data = json.loads(raw.strip())

    result = FeynmanScore(
        session_id=session_id,
        candidate_id=session["candidate_id"],
        topic_id=topic_id,
        clarity=data.get("clarity", 0),
        patience=data.get("patience", 0),
        empathy=data.get("empathy", 0),
        adaptability=data.get("adaptability", 0),
        quiz_transfer_score=data.get("quiz_transfer_score", 0),
        overall_score=data.get("overall_score", 0),
        summary=data.get("summary", ""),
        message_count=session["exchange_count"],
        quiz_answers=parsed_quiz,
    )

    _score_cache[session["candidate_id"]] = result

    # Clean up session
    del _sessions[session_id]

    return result


@router.get("/score/{candidate_id}", response_model=FeynmanScore | None)
def get_score(candidate_id: str):
    """Get the Feynman teaching score for a candidate."""
    return _score_cache.get(candidate_id)
