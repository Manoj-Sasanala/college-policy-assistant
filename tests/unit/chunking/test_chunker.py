import json
from pathlib import Path

import pytest

from app.chunking.chunker import chunk_source
from app.ingestion.source_validator import validate_source

FIXTURE = Path("data/fixtures/c01_attendance_policy.json")


def _validated() -> dict:
    return validate_source(json.loads(FIXTURE.read_text(encoding="utf-8")))


def test_chunk_matches_c03_required_fields():
    src = _validated()
    chunks = chunk_source(src)
    assert len(chunks) == 1
    chunk = chunks[0]
    for field in (
        "chunk_id",
        "text",
        "document_id",
        "document_title",
        "section",
        "source",
    ):
        assert chunk[field], f"{field} must be non-empty"


def test_chunk_id_is_deterministic():
    src = _validated()
    a = chunk_source(src)
    b = chunk_source(src)
    assert [c["chunk_id"] for c in a] == [c["chunk_id"] for c in b]
    assert [c["text"] for c in a] == [c["text"] for c in b]


def test_chunk_id_format():
    src = _validated()
    chunk = chunk_source(src)[0]
    assert chunk["chunk_id"] == "attendance-policy-examination-eligibility-001"


def test_metadata_propagates_from_c01():
    src = _validated()
    chunk = chunk_source(src)[0]
    assert chunk["document_id"] == src["document_id"]
    assert chunk["document_title"] == src["document_title"]
    assert chunk["section"] == src["section"]
    assert chunk["page"] == src["page"]
    assert chunk["version"] == src["version"]
    assert chunk["effective_date"] == src["effective_date"]
    assert chunk["source"] == src["source"]


def test_no_condition_is_dropped():
    src = _validated()
    chunk = chunk_source(src)[0]
    assert "75%" in chunk["text"]
    assert "65-74%" in chunk["text"]
    assert "condonation" in chunk["text"]
    assert "approval" in chunk["text"]


def test_empty_text_rejected():
    with pytest.raises(Exception):
        chunk_source(
            {
                "document_id": "x",
                "document_title": "X",
                "section": "S",
                "source": "s",
                "original_text": "   ",
            }
        )