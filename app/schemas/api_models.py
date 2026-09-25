"""L5 — API schemas for C06 Policy Question API.

These models define the exact request/response shape described in 9.6.
They are not the contract source of truth; they implement it.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

StatusLiteral = Literal["grounded", "insufficient_evidence", "invalid_request", "service_error"]


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)

    @field_validator("question")
    @classmethod
    def _strip_nonempty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("question must be a non-empty string")
        return v


class Source(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    section: str
    page: Optional[int] = None


class AskResponse(BaseModel):
    status: StatusLiteral
    answer: str
    sources: list[Source] = Field(default_factory=list)


class FailureResponse(BaseModel):
    status: Literal["service_error"] = "service_error"
    error_code: Literal[
        "INVALID_REQUEST",
        "RETRIEVAL_UNAVAILABLE",
        "GENERATION_UNAVAILABLE",
        "CONFIGURATION_ERROR",
        "INTERNAL_ERROR",
    ]
    message: str
    retryable: bool
