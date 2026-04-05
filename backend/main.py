"""InVision U — Intelligent Candidate Selection Support System API."""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import analysis, auth, candidates, feynman, scoring

app = FastAPI(
    title="InVision U Candidate Scoring API",
    description="AI-powered candidate evaluation for inVision U admissions committee",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(candidates.router)
app.include_router(scoring.router)
app.include_router(analysis.router)
app.include_router(feynman.router)


@app.get("/")
def root():
    return {
        "name": "InVision U Candidate Scoring API",
        "version": "1.0.0",
        "docs": "/docs",
    }
