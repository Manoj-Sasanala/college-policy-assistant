from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_grounded_attendance_question():
    r = client.post("/api/ask", json={"question": "My attendance is 70%. Can I write the semester examination?"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "grounded"
    assert body["answer"].strip() != ""
    assert isinstance(body["sources"], list)
    assert len(body["sources"]) == 1
    src = body["sources"][0]
    assert src["chunk_id"] == "attendance-policy-exam-eligibility-001"
    assert src["document_id"] == "attendance-policy"
    assert src["document_title"] == "Attendance Policy"
    assert src["section"] == "Examination Eligibility"


def test_unsupported_question_returns_insufficient():
    r = client.post("/api/ask", json={"question": "What is the maximum number of condonation applications a student can submit?"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "insufficient_evidence"
    assert body["sources"] == []


def test_empty_question_rejected():
    r = client.post("/api/ask", json={"question": "   "})
    assert r.status_code in (400, 422)


def test_missing_question_rejected():
    r = client.post("/api/ask", json={})
    assert r.status_code in (400, 422)


def test_answer_preserves_conditions():
    r = client.post("/api/ask", json={"question": "My attendance is 70%. Can I write the semester examination?"})
    body = r.json()
    text = body["answer"]
    assert "75%" in text
    assert "65-74%" in text
    assert "condonation" in text
    assert "approval" in text


def test_no_source_is_fabricated_for_insufficient():
    r = client.post("/api/ask", json={"question": "What is the library timing?"})
    body = r.json()
    assert body["status"] == "insufficient_evidence"
    assert body["sources"] == []
