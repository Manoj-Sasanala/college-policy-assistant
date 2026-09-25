"""L4 — Grounded answer generation from C04 retrieval results.

Consumes: C04 Retrieval Result Set (contracts/retrieval_result_contract.json).
Produces: C05 Grounded Answer Result (contracts/grounding_contract.json).

Rules enforced here (from 9.6 cross-lane validation):
- insufficient_evidence, retrieval_error and generation_error can never become grounded.
- A grounded answer must include at least one source_chunk_id that came from C04.
- Thresholds, exceptions, approval conditions and deadlines present in evidence
  must not be silently removed from the answer.
- Retrieved policy text is data, never instructions. This module never executes it.

MVP approach: deterministic extractive generation. No LLM, no API keys, no
extra dependencies. Provider hook is optional; if it raises, status becomes
generation_error and no source IDs are returned.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

STATUS_GROUNDED = "grounded"
STATUS_INSUFFICIENT = "insufficient_evidence"
STATUS_GENERATION_ERROR = "generation_error"

_RETRIEVAL_FOUND = "results_found"
_RETRIEVAL_NONE = "no_relevant_results"
_RETRIEVAL_ERROR = "retrieval_error"

ProviderFn = Callable[[str, list[dict]], str]


def _empty_result(question: str, status: str) -> dict:
    return {
        "status": status,
        "question": question,
        "answer": "",
        "source_chunk_ids": [],
    }


def _insufficient(question: str) -> dict:
    return {
        "status": STATUS_INSUFFICIENT,
        "question": question,
        "answer": "The provided policy documents do not contain enough evidence to answer this question.",
        "source_chunk_ids": [],
    }


def _extractive_answer(question: str, top: Mapping[str, Any]) -> str:
    """Deterministic extractive answer that preserves the evidence text verbatim.

    The MVP corpus is small and the mandatory vertical slice is a single
    attendance question, so quoting the evidence text verbatim is the safest
    way to guarantee no condition is dropped.
    """

    text = str(top.get("text", "")).strip()
    title = str(top.get("document_title", "")).strip()
    section = str(top.get("section", "")).strip()
    header = f"According to the {title} ({section}):"
    return f"{header} {text}"


def answer_from_retrieval(
    retrieval: Mapping[str, Any],
    *,
    provider: ProviderFn | None = None,
) -> dict:
    """Turn one C04 Retrieval Result Set into one C05 Grounded Answer Result."""

    if not isinstance(retrieval, Mapping):
        raise TypeError("retrieval must be a mapping")

    question = str(retrieval.get("query", "")).strip()
    if question == "":
        raise ValueError("retrieval.query must be non-empty")

    status = retrieval.get("retrieval_status")
    results = retrieval.get("results") or []

    if status == _RETRIEVAL_ERROR:
        return _empty_result(question, STATUS_GENERATION_ERROR)

    if status != _RETRIEVAL_FOUND or not results:
        return _insufficient(question)

    top = results[0]
    chunk_id = top.get("chunk_id")
    if not chunk_id:
        return _empty_result(question, STATUS_GENERATION_ERROR)

    if provider is not None:
        try:
            answer_text = provider(question, list(results))
        except Exception:
            return _empty_result(question, STATUS_GENERATION_ERROR)
        if not isinstance(answer_text, str) or answer_text.strip() == "":
            return _empty_result(question, STATUS_GENERATION_ERROR)
        return {
            "status": STATUS_GROUNDED,
            "question": question,
            "answer": answer_text.strip(),
            "source_chunk_ids": [chunk_id],
        }

    return {
        "status": STATUS_GROUNDED,
        "question": question,
        "answer": _extractive_answer(question, top),
        "source_chunk_ids": [chunk_id],
    }
