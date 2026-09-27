"""InVision U — Intelligent Candidate Selection Support System API."""

from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import settings
from backend.db.engine import assert_schema_current
from backend.routers import analysis, auth, candidates, committee, evaluation, fairness, feynman, heldout, historical, ledger, overrides, scoring
from backend.security import check_auth_config


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Refuse to start on a database that is missing or behind the code, with
    # the command that fixes it, instead of failing on the first request.
    assert_schema_current()
    # Same for auth: no AUTH_SECRET, or the repo's dev secret outside
    # DEMO_MODE, stops startup here rather than at the first login.
    check_auth_config()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="InVision U Candidate Scoring API",
    description="AI-powered candidate evaluation for inVision U admissions committee",
    version="1.0.0",
)

# The token travels in the Authorization header, not a cookie, so the browser
# needs no credentials mode; only the listed frontends may call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(candidates.router)
app.include_router(scoring.router)
app.include_router(analysis.router)
app.include_router(feynman.router)
app.include_router(overrides.router)
app.include_router(committee.router)
app.include_router(ledger.router)
app.include_router(fairness.router)
app.include_router(evaluation.router)
app.include_router(historical.router)
app.include_router(heldout.router)


@app.get("/")
def root():
    return {
        "name": "InVision U Candidate Scoring API",
        "version": "1.0.0",
        "docs": "/docs",
    }
