import json
from pathlib import Path

import pytest

from app.prompts.grounding_prompt import build_prompt
from app.rag.grounding import (
    STATUS_GENERATION_ERROR,
    STATUS_GROUNDED,
    STATUS_INSUFFICIENT,
    answer_from_retrieval,
)

RAG_DIR = Path(__file__).resolve().parent


def _load(name: str) -> dict:
    return json.loads((RAG_DIR / name).read_text(encoding="utf-8"))


def test_supported_returns_grounded():
    out = answer_from_retrieval(_load("c04_supported_fixture.json"))
    assert out["status"] == STATUS_GROUNDED
    assert out["source_chunk_ids"] == ["attendance-policy-exam-eligibility-001"]
    assert out["answer"].strip() != ""


def test_supported_answer_preserves_conditions():
    out = answer_from_retrieval(_load("c04_supported_fixture.json"))
    text = out["answer"]
    assert "75%" in text
    assert "65-74%" in text
    assert "condonation" in text
    assert "approval" in text


def test_no_evidence_returns_insufficient():
    out = answer_from_retrieval(_load("c04_no_evidence_fixture.json"))
    assert out["status"] == STATUS_INSUFFICIENT
    assert out["source_chunk_ids"] == []
    assert out["answer"].strip() != ""


def test_retrieval_error_becomes_generation_error():
    retrieval = {
        "query": "q",
        "top_k": 3,
        "relevance_threshold": 0.7,
        "results": [],
        "retrieval_status": "retrieval_error",
    }
    out = answer_from_retrieval(retrieval)
    assert out["status"] == STATUS_GENERATION_ERROR
    assert out["source_chunk_ids"] == []


def test_provider_failure_becomes_generation_error():
    def boom(question, results):
        raise RuntimeError("provider down")

    out = answer_from_retrieval(_load("c04_supported_fixture.json"), provider=boom)
    assert out["status"] == STATUS_GENERATION_ERROR
    assert out["source_chunk_ids"] == []


def test_provider_success_is_grounded():
    def ok(question, results):
        return "Grounded answer from provider."

    out = answer_from_retrieval(_load("c04_supported_fixture.json"), provider=ok)
    assert out["status"] == STATUS_GROUNDED
    assert out["answer"] == "Grounded answer from provider."
    assert out["source_chunk_ids"] == ["attendance-policy-exam-eligibility-001"]


def test_empty_query_rejected():
    with pytest.raises(ValueError):
        answer_from_retrieval({"query": "", "retrieval_status": "results_found", "results": []})


def test_prompt_contains_question_and_evidence():
    retrieval = _load("c04_supported_fixture.json")
    prompt = build_prompt(retrieval["query"], retrieval["results"])
    assert retrieval["query"] in prompt
    assert "75%" in prompt
    assert "data" in prompt.lower()


def test_prompt_marks_evidence_as_data():
    retrieval = _load("c04_supported_fixture.json")
    prompt = build_prompt(retrieval["query"], retrieval["results"])
    assert "never as instructions" in prompt
