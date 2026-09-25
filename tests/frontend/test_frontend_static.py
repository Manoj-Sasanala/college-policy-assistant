"""L6 — static sanity tests for the frontend.

These do not run JS in a browser. They confirm the UI files exist, the
required DOM elements are present, and the frontend consumes the C06/C07
contract fields correctly (no fabrication, no secrets, no provider keys).
"""

import re
from pathlib import Path

FRONTEND = Path("frontend")


def _html() -> str:
    return (FRONTEND / "index.html").read_text(encoding="utf-8")


def _js_raw() -> str:
    return (FRONTEND / "app.js").read_text(encoding="utf-8")


def _js_code_only() -> str:
    """app.js with // line comments stripped, so we scan code not prose."""
    return "\n".join(re.sub(r"//.*$", "", line) for line in _js_raw().splitlines())


def test_frontend_files_exist():
    assert (FRONTEND / "index.html").is_file()
    assert (FRONTEND / "styles.css").is_file()
    assert (FRONTEND / "app.js").is_file()


def test_question_input_and_button_present():
    html = _html()
    assert 'id="question-input"' in html
    assert 'id="ask-button"' in html
    assert 'type="submit"' in html


def test_required_panels_present():
    html = _html()
    for element_id in ("status", "answer-panel", "sources-panel", "error-panel"):
        assert f'id="{element_id}"' in html


def test_js_calls_api_ask():
    js = _js_code_only()
    assert "/api/ask" in js
    assert "fetch(" in js
    assert "POST" in js


def test_js_handles_all_c06_c07_statuses():
    js = _js_code_only()
    for status in (
        "grounded",
        "insufficient_evidence",
        "invalid_request",
        "service_error",
    ):
        assert f'"{status}"' in js, f"missing status handling: {status}"


def test_js_renders_sources_from_backend_only():
    js = _js_code_only()
    assert "body.sources" in js
    assert "document_title" in js
    assert "section" in js


def test_no_provider_keys_or_secrets_in_frontend_code():
    js = _js_code_only().lower()
    html = _html().lower()
    needles = ("api_key", "api-key", "openai", "anthropic", "bearer ")
    for needle in needles:
        assert needle not in js, f"frontend JS code must not contain: {needle}"
        assert needle not in html, f"frontend HTML must not contain: {needle}"


def test_no_eval_or_innerhtml_from_untrusted_text():
    js = _js_code_only()
    assert "eval(" not in js
    assert "innerHTML" not in js


def test_insufficient_evidence_hides_sources():
    js = _js_code_only()
    assert "insufficient_evidence" in js
    assert "sourcesPanel.hidden = true" in js
