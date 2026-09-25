"""L2 — Deterministic chunking of C01 records into C03 chunk records.

Consumes: validated C01 Policy Source Record.
Produces: list of C03 Policy Chunk Records (see contracts/chunk_contract.json).

Determinism rules:
- same input -> same chunk_id and same text, every run
- chunk_id derives from document_id, section slug, and index
- original policy conditions are preserved verbatim in chunk text
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from app.ingestion.source_validator import SourceValidationError

MAX_CHARS = 800


def _slug(value: str) -> str:
    """Lowercase, alphanumeric-and-hyphen slug for chunk_id parts."""

    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "section"


def _split_preserving_conditions(text: str) -> list[str]:
    """Split text into deterministic chunks while preserving every sentence.

    Strategy (MVP): keep the whole section text as one chunk unless it exceeds
    MAX_CHARS. If it exceeds, split on sentence boundaries so no sentence is
    dropped. Never drop a condition, threshold, exception or approval clause.
    """

    text = text.strip()
    if text == "":
        raise SourceValidationError("empty_chunk: original_text is empty")
    if len(text) <= MAX_CHARS:
        return [text]

    parts = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""
    for part in parts:
        candidate = (current + " " + part).strip() if current else part
        if len(candidate) <= MAX_CHARS:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = part
    if current:
        chunks.append(current)
    return chunks


def chunk_source(record: Mapping[str, Any], *, start_index: int = 1) -> list[dict]:
    """Turn one validated C01 record into C03 chunk records."""

    doc_id = record["document_id"]
    section = record["section"]
    section_slug = _slug(section)

    pieces = _split_preserving_conditions(record["original_text"])

    chunks: list[dict] = []
    for offset, piece in enumerate(pieces):
        index = start_index + offset
        chunk_id = f"{doc_id}-{section_slug}-{index:03d}"
        chunks.append(
            {
                "chunk_id": chunk_id,
                "text": piece,
                "document_id": doc_id,
                "document_title": record["document_title"],
                "section": section,
                "page": record.get("page"),
                "version": record.get("version"),
                "effective_date": record.get("effective_date"),
                "source": record["source"],
            }
        )
    return chunks
    