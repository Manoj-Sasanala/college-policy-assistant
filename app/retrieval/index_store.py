"""L3 — Save/load the local retrieval index.

The index is a JSON artifact containing the C03 chunks plus their
deterministic embeddings. No database, no hosted service, no pickle.

Format:
{
  "index_version": 1,
  "embed_dim": 256,
  "chunks": [ <C03 chunk>, ... ],
  "vectors": [ [float, ...], ... ]
}
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from app.embeddings.embedder import EMBED_DIM, embed_text
from app.retrieval.retriever import Retriever, _require_chunk

INDEX_VERSION = 1


class IndexError(RuntimeError):
    """Raised for index build/load problems."""


def build_index(chunks: list[Mapping[str, Any]]) -> dict:
    safe_chunks = [_require_chunk(c) for c in chunks]
    vectors = [embed_text(c["text"]) for c in safe_chunks]
    return {
        "index_version": INDEX_VERSION,
        "embed_dim": EMBED_DIM,
        "chunks": safe_chunks,
        "vectors": vectors,
    }


def save_index(index: Mapping[str, Any], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")


def load_index(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise IndexError("index file must be a JSON object")
    if data.get("index_version") != INDEX_VERSION:
        raise IndexError(f"unsupported index_version: {data.get('index_version')}")
    if data.get("embed_dim") != EMBED_DIM:
        raise IndexError(f"index embed_dim mismatch: {data.get('embed_dim')}")
    return dict(data)


def retriever_from_index(index: Mapping[str, Any]) -> Retriever:
    """Build a Retriever from a loaded index without recomputing embeddings."""

    chunks = index.get("chunks") or []
    vectors = index.get("vectors") or []
    if len(chunks) != len(vectors):
        raise IndexError("index chunks/vectors length mismatch")

    r = Retriever([])
    r._chunks = [_require_chunk(c) for c in chunks]  # type: ignore[attr-defined]
    r._vectors = [list(v) for v in vectors]          # type: ignore[attr-defined]
    return r
