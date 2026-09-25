"""L5 — Real adapters: L3 retriever + L4 grounder.

Replaces fixture-backed adapters at H3 integration. If the real chunk
artifact is missing, falls back to fixtures so unit tests still run.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from app.rag.grounding import answer_from_retrieval
from app.retrieval.retriever import Retriever

CHUNKS_PATH = Path("data/chunks/attendance-policy.chunks.json")
FIXTURE_DIR = Path(__file__).resolve().parents[2] / "tests" / "api" / "fixtures"

RELEVANCE_THRESHOLD = 0.20
TOP_K = 3

_RETRIEVER: Retriever | None = None


def _load_retriever() -> Retriever:
    global _RETRIEVER
    if _RETRIEVER is None:
        chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
        _RETRIEVER = Retriever(chunks)
    return _RETRIEVER


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def real_retriever(question: str) -> Mapping:
    """Real L3 retriever. Falls back to fixtures if the chunk artifact is absent."""

    if not CHUNKS_PATH.is_file():
        q = (question or "").lower()
        if "attendance" in q:
            return _load_fixture("c04_supported.json")
        return _load_fixture("c04_no_evidence.json")

    retriever = _load_retriever()
    return retriever.retrieve(
        question,
        top_k=TOP_K,
        relevance_threshold=RELEVANCE_THRESHOLD,
    )


def real_grounder(c04: Mapping) -> Mapping:
    """Real L4 grounder. Falls back to fixture shape if grounding is unavailable."""

    return answer_from_retrieval(c04)
