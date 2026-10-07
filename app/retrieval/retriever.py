"""L3 — Local deterministic retrieval over C03 chunks.

Consumes: C03 Policy Chunk Record(s) (from data/chunks/*.json or C03 fixture).
Produces: C04 Retrieval Result Set (see contracts/retrieval_result_contract.json).

Stdlib-only, no external services, no model downloads, no API keys.
Deterministic ordering: sort by descending score, ties broken by chunk_id.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from app.embeddings.embedder import cosine, embed_text

DEFAULT_TOP_K = 3
DEFAULT_THRESHOLD = 0.0

RETRIEVAL_STATUS_FOUND = "results_found"
RETRIEVAL_STATUS_NONE = "no_relevant_results"
RETRIEVAL_STATUS_ERROR = "retrieval_error"

_C03_FIELDS = (
    "chunk_id",
    "text",
    "document_id",
    "document_title",
    "section",
    "page",
    "version",
    "effective_date",
    "source",
)


class RetrievalError(RuntimeError):
    """Raised for retrieval configuration/usage errors."""


def _require_chunk(chunk: Mapping[str, Any]) -> dict:
    if not isinstance(chunk, Mapping):
        raise RetrievalError("chunk must be a mapping")
    for field in ("chunk_id", "text", "document_id", "document_title", "section", "source"):
        if not chunk.get(field):
            raise RetrievalError(f"chunk missing required field: {field}")
    out: dict = {}
    for field in _C03_FIELDS:
        out[field] = chunk.get(field)
    return out


def load_chunks(path: str | Path) -> list[dict]:
    """Load a JSON file containing a list of C03 chunks (or a single C03 chunk)."""

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, Mapping):
        data = [data]
    if not isinstance(data, list):
        raise RetrievalError("chunk file must contain a C03 chunk or list of chunks")
    return [_require_chunk(c) for c in data]


class Retriever:
    """In-memory retriever. Chunks are provided; embeddings are computed once."""

    def __init__(self, chunks: Iterable[Mapping[str, Any]]):
        self._chunks: list[dict] = []
        self._vectors: list[list[float]] = []
        for chunk in chunks:
            safe = _require_chunk(chunk)
            self._chunks.append(safe)
            self._vectors.append(embed_text(safe["text"]))

    @property
    def chunks(self) -> list[dict]:
        return list(self._chunks)

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = DEFAULT_TOP_K,
        relevance_threshold: float = DEFAULT_THRESHOLD,
    ) -> dict:
        if not isinstance(query, str) or query.strip() == "":
            raise RetrievalError("query must be a non-empty string")
        if not isinstance(top_k, int) or top_k <= 0:
            raise RetrievalError("top_k must be a positive integer")

        try:
            qvec = embed_text(query)
            scored: list[tuple[float, dict]] = []
            for chunk, cvec in zip(self._chunks, self._vectors):
                score = cosine(qvec, cvec)
                if score >= relevance_threshold:
                    scored.append((score, chunk))
            scored.sort(key=lambda pair: (-pair[0], pair[1]["chunk_id"]))
            top = scored[:top_k]

            results: list[dict] = []
            for score, chunk in top:
                results.append(
                    {
                        "chunk_id": chunk["chunk_id"],
                        "score": score,
                        "text": chunk["text"],
                        "document_id": chunk["document_id"],
                        "document_title": chunk["document_title"],
                        "section": chunk["section"],
                        "page": chunk["page"],
                        "version": chunk["version"],
                        "effective_date": chunk["effective_date"],
                        "source": chunk["source"],
                    }
                )

            status = RETRIEVAL_STATUS_FOUND if results else RETRIEVAL_STATUS_NONE
            return {
                "query": query,
                "top_k": top_k,
                "relevance_threshold": relevance_threshold,
                "results": results,
                "retrieval_status": status,
            }
        except Exception as exc:
            raise RetrievalError(f"retrieval failed: {exc}") from exc
