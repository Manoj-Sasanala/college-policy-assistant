import json
from pathlib import Path

import pytest

from app.embeddings.embedder import EMBED_DIM, cosine, embed_text
from app.retrieval.retriever import RetrievalError, Retriever, load_chunks

FIXTURE = Path("tests/fixtures/retrieval/c03_chunk_fixture.json")


def _retriever() -> Retriever:
    return Retriever(load_chunks(FIXTURE))


def test_embedding_is_deterministic():
    a = embed_text("attendance 75%")
    b = embed_text("attendance 75%")
    assert a == b
    assert len(a) == EMBED_DIM


def test_embedding_is_unit_length():
    v = embed_text("attendance policy")
    norm = sum(x * x for x in v) ** 0.5
    assert abs(norm - 1.0) < 1e-9


def test_cosine_self_is_one():
    v = embed_text("attendance policy")
    assert abs(cosine(v, v) - 1.0) < 1e-9


def test_retrieve_returns_c04_fields():
    r = _retriever()
    out = r.retrieve("My attendance is 70%. Can I write the semester examination?", top_k=3, relevance_threshold=0.0)
    for field in ("query", "top_k", "relevance_threshold", "results", "retrieval_status"):
        assert field in out
    assert out["retrieval_status"] == "results_found"
    assert len(out["results"]) == 1
    row = out["results"][0]
    for field in ("chunk_id", "score", "text", "document_id", "document_title", "section", "source"):
        assert row[field] not in (None, "")


def test_empty_query_rejected():
    r = _retriever()
    with pytest.raises(RetrievalError):
        r.retrieve("   ")


def test_bad_top_k_rejected():
    r = _retriever()
    with pytest.raises(RetrievalError):
        r.retrieve("attendance", top_k=0)


def test_no_relevant_results_when_threshold_high():
    r = _retriever()
    out = r.retrieve("attendance", top_k=3, relevance_threshold=0.999999)
    assert out["retrieval_status"] == "no_relevant_results"
    assert out["results"] == []


def test_deterministic_ordering():
    r = _retriever()
    a = r.retrieve("attendance", top_k=3, relevance_threshold=0.0)
    b = r.retrieve("attendance", top_k=3, relevance_threshold=0.0)
    assert [x["chunk_id"] for x in a["results"]] == [x["chunk_id"] for x in b["results"]]
