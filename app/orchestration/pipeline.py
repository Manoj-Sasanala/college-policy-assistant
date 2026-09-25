"""L5 — Orchestration: question -> C06 response.

Inputs (injected, so this module does not depend on L3/L4 being on this branch):
- retriever: callable (question) -> C04 Retrieval Result Set (dict)
- grounder:  callable (C04 dict) -> C05 Grounded Answer Result (dict)

Output: C06 Policy Question API response (dict), backend-assembled citations.

Rules enforced here (from 9.6):
- L5 owns citation assembly. L6 never creates sources.
- grounded requires at least one source whose chunk_id came from C04 evidence.
- insufficient_evidence must have an empty source list.
- service_error is never grounded.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

from app.schemas.api_models import AskResponse, FailureResponse, Source

RetrieverFn = Callable[[str], Mapping[str, Any]]
GrounderFn = Callable[[Mapping[str, Any]], Mapping[str, Any]]


def _sources_from_c04(c04: Mapping[str, Any], allowed_chunk_ids: list[str]) -> list[dict]:
    """Build backend-owned citation list from C04 evidence metadata.

    Only chunk_ids that C05 returned as evidence are included.
    """

    allowed = set(allowed_chunk_ids)
    results = c04.get("results") or []
    sources: list[dict] = []
    for row in results:
        if not isinstance(row, Mapping):
            continue
        cid = row.get("chunk_id")
        if cid not in allowed:
            continue
        sources.append(
            {
                "chunk_id": cid,
                "document_id": row.get("document_id"),
                "document_title": row.get("document_title"),
                "section": row.get("section"),
                "page": row.get("page"),
            }
        )
    return sources


def _failure(error_code: str, message: str, retryable: bool) -> dict:
    return FailureResponse(
        error_code=error_code,  # type: ignore[arg-type]
        message=message,
        retryable=retryable,
    ).model_dump()


def handle_question(
    question: str,
    *,
    retriever: RetrieverFn,
    grounder: GrounderFn,
) -> dict:
    """Full orchestration for POST /api/ask."""

    if not isinstance(question, str) or question.strip() == "":
        return _failure("INVALID_REQUEST", "Question must be a non-empty string.", retryable=False)

    try:
        c04 = retriever(question)
    except Exception:
        return _failure(
            "RETRIEVAL_UNAVAILABLE",
            "The policy search service is temporarily unavailable.",
            retryable=True,
        )

    if not isinstance(c04, Mapping):
        return _failure("INTERNAL_ERROR", "Retrieval returned an invalid result.", retryable=False)

    if c04.get("retrieval_status") == "retrieval_error":
        return _failure(
            "RETRIEVAL_UNAVAILABLE",
            "The policy search service is temporarily unavailable.",
            retryable=True,
        )

    try:
        c05 = grounder(c04)
    except Exception:
        return _failure(
            "GENERATION_UNAVAILABLE",
            "The answer generation service is temporarily unavailable.",
            retryable=True,
        )

    if not isinstance(c05, Mapping):
        return _failure("INTERNAL_ERROR", "Grounding returned an invalid result.", retryable=False)

    status = c05.get("status")
    answer = str(c05.get("answer", "") or "")
    evidence_ids = list(c05.get("source_chunk_ids") or [])

    if status == "generation_error":
        return _failure(
            "GENERATION_UNAVAILABLE",
            "The answer generation service is temporarily unavailable.",
            retryable=True,
        )

    if status == "insufficient_evidence":
        resp = AskResponse(
            status="insufficient_evidence",
            answer=answer or "The provided policy documents do not contain enough evidence.",
            sources=[],
        )
        return resp.model_dump()

    if status == "grounded":
        if not evidence_ids:
            return _failure("INTERNAL_ERROR", "Grounded answer had no evidence IDs.", retryable=False)
        sources_payload = _sources_from_c04(c04, evidence_ids)
        if not sources_payload:
            return _failure(
                "INTERNAL_ERROR",
                "Grounded answer referenced evidence not present in retrieval results.",
                retryable=False,
            )
        resp = AskResponse(
            status="grounded",
            answer=answer,
            sources=[Source(**s) for s in sources_payload],
        )
        return resp.model_dump()

    return _failure("INTERNAL_ERROR", "Unknown grounding status.", retryable=False)
