import json
from pathlib import Path

import pytest

from app.ingestion.source_validator import (
    SourceValidationError,
    validate_source,
)

FIXTURE = Path("data/fixtures/c01_attendance_policy.json")


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_fixture_validates():
    result = validate_source(_fixture())
    assert result["document_id"] == "attendance-policy"
    assert result["section"] == "Examination Eligibility"
    assert result["original_text"].startswith("Students must maintain")


def test_missing_required_field_rejected():
    bad = _fixture()
    del bad["document_id"]
    with pytest.raises(SourceValidationError):
        validate_source(bad)


def test_empty_text_rejected():
    bad = _fixture()
    bad["original_text"] = "   "
    with pytest.raises(SourceValidationError):
        validate_source(bad)


def test_bad_page_rejected():
    bad = _fixture()
    bad["page"] = 0
    with pytest.raises(SourceValidationError):
        validate_source(bad)


def test_null_page_allowed():
    good = _fixture()
    good["page"] = None
    result = validate_source(good)
    assert result["page"] is None