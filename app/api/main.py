"""L5 — FastAPI app: POST /api/ask + serves the L6 frontend at /.

H3 integration: uses real L3 retriever + real L4 grounder.
Same-origin: frontend is served from this server so browser fetch works.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.adapters import real_grounder, real_retriever
from app.orchestration.pipeline import handle_question
from app.schemas.api_models import AskRequest

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

app = FastAPI(title="College Policy Assistant API", version="0.3.0")

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
    return handle_question(
        request.question,
        retriever=real_retriever,
        grounder=real_grounder,
    )


if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
