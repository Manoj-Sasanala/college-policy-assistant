"""L5 — FastAPI application exposing POST /api/ask.

Consumes: C05 Grounded Answer Result (via orchestration pipeline).
Produces: C06 Policy Question API response, or C07 Runtime Failure Result.

Run locally:
    python -m uvicorn app.api.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.adapters import fixture_grounder, fixture_retriever
from app.orchestration.pipeline import handle_question
from app.schemas.api_models import AskRequest

app = FastAPI(title="College Policy Assistant API", version="0.1.0")

# Frontend (L6) runs locally during H0-H3. MVP permissive CORS; L5 owns this.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/ask")
def ask(request: AskRequest) -> dict:
    """Accept a user question and return a C06 response (or C07 failure)."""

    return handle_question(
        request.question,
        retriever=fixture_retriever,
        grounder=fixture_grounder,
    )
