"""L3 — Deterministic local embedder.

Stdlib-only: no numpy, no model download, no API keys, no provider.
Deterministic: same text -> same vector, every run, on every machine.

Method: hashing bag-of-words into a fixed-dimension vector with
L2 normalization. Sufficient for the MVP corpus size and for
cosine-similarity retrieval.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Iterable

EMBED_DIM = 256

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _bucket(token: str) -> int:
    digest = hashlib.sha1(token.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % EMBED_DIM


def embed_text(text: str) -> list[float]:
    """Return a deterministic unit-length embedding for text."""

    if text is None:
        text = ""
    tokens = _tokenize(text)
    vec = [0.0] * EMBED_DIM
    for token in tokens:
        vec[_bucket(token)] += 1.0
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        return vec
    return [v / norm for v in vec]


def embed_many(texts: Iterable[str]) -> list[list[float]]:
    return [embed_text(t) for t in texts]


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity for two same-dimension vectors."""

    if len(a) != len(b):
        raise ValueError("vector length mismatch")
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))
