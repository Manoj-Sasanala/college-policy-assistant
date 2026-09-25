"""L2 — Source validation for C01 Policy Source Records.

Consumes: C01 Policy Source Record (contracts/policy_source_contract.json)
Produces: validated C01 dict, or raises SourceValidationError.

This module never invents policy content. It only checks presence and shape
of the C01 fields defined in 9.6.
"""

from __future__ import annotations

from typing import Any, Mapping

REQUIRED_FIELDS = (
    "document_id",
    "document_title",
    "section",
    "source",
    "original_text",
)

OPTIONAL_FIELDS = (
    "page",
    "version",
    "effective_date",
)

ALLOWED_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS


class SourceValidationError(ValueError):
    """Raised when a C01 record fails validation."""


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def validate_source(record: Mapping[str, Any]) -> dict:
    """Validate a C01 Policy Source Record.

    Returns a new dict containing only the allowed C01 fields, with the
    original_text preserved exactly.
    """

    if not isinstance(record, Mapping):
        raise SourceValidationError("C01 record must be a mapping")

    for field in REQUIRED_FIELDS:
        if field not in record:
            raise SourceValidationError(f"missing required field: {field}")
        if not _is_non_empty_string(record[field]):
            raise SourceValidationError(f"field must be non-empty string: {field}")

    page = record.get("page")
    if page is not None:
        if not isinstance(page, int) or isinstance(page, bool) or page <= 0:
            raise SourceValidationError("page must be a positive integer when present")

    for field in ("version", "effective_date"):
        value = record.get(field)
        if value is not None and not _is_non_empty_string(value):
            raise SourceValidationError(f"{field} must be non-empty string or null")

    validated: dict = {}
    for field in ALLOWED_FIELDS:
        validated[field] = record.get(field)
    return validated