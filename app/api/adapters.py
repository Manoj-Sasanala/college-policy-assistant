"""L5 — Fixture-backed adapters for H0–H3.

At H3 these are replaced by real L3 (retrieval) and L4 (grounding) modules.
They exist so L5's API and orchestration can be built and tested before
upstream branches are merged.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "tests" / "api" / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def fixture_retriever(question: str) -> Mapping:
    """Return a C04 Retrieval Result Set for the given question.

    MVP heuristic: if the question mentions 'attendance', return the supported
    fixture; otherwise return the no-evidence fixture.
    """

    q = (question or "").lower()
    if "attendance" in q:
        return _load("c04_supported.json")
    return _load("c04_no_evidence.json")


def fixture_grounder(c04: Mapping) -> Mapping:
    """Return a C05 Grounded Answer Result built from the C04 evidence."""

    status = c04.get("retrieval_status")
    results = c04.get("results") or []
    if status != "results_found" or not results:
        return {
            "status": "insufficient_evidence",
            "question": c04.get("query", ""),
            "answer": "The provided policy documents do not contain enough evidence to answer this question.",
            "source_chunk_ids": [],
        }
    top = results[0]
    return {
        "status": "grounded",
        "question": c04.get("query", ""),
        "answer": f"According to the {top.get('document_title')} ({top.get('section')}): {top.get('text')}",
        "source_chunk_ids": [top.get("chunk_id")],
    }
