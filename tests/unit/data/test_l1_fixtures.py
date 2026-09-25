import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_c01_fixture_has_required_fields():
    rec = _load("data/fixtures/c01_policy_source_record_example.json")
    for field in (
        "document_id",
        "document_title",
        "section",
        "source",
        "original_text",
    ):
        assert rec[field], f"{field} must be non-empty"


def test_c01_fixture_preserves_all_policy_conditions():
    rec = _load("data/fixtures/c01_policy_source_record_example.json")
    text = rec["original_text"]
    assert "75%" in text
    assert "65-74%" in text
    assert "condonation" in text
    assert "approval" in text


def test_c01_fixture_matches_source_text():
    rec = _load("data/fixtures/c01_policy_source_record_example.json")
    raw = (ROOT / "data/policies/attendance-policy.txt").read_text(encoding="utf-8")
    assert rec["original_text"] in raw


def test_c02_supported_fixture():
    rec = _load("data/fixtures/c02_attendance_70_supported.json")
    assert rec["expected_status"] == "grounded"
    assert rec["expected_source_document_id"] == "attendance-policy"
    assert rec["human_verification_required"] is True


def test_c02_unsupported_fixture():
    rec = _load("data/fixtures/c02_condonation_count_unsupported.json")
    assert rec["expected_status"] == "insufficient_evidence"
    assert rec["expected_source_document_id"] is None
    assert rec["expected_policy_facts"] == []


def test_manifest_references_real_source():
    manifest = _load("data/source_manifest.json")
    assert manifest["documents"], "manifest must list at least one document"
    for doc in manifest["documents"]:
        assert (ROOT / doc["source_file"]).is_file()