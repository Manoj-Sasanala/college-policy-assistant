"""VALIDATE-01 — critical end-to-end scenarios via FastAPI TestClient."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)

results = []


def check(name, ok, detail):
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")


# 1. Happy path
r = client.post("/api/ask", json={"question": "My attendance is 70%. Can I write the semester examination?"})
b = r.json()
check(
    "1 happy-path grounded",
    r.status_code == 200 and b.get("status") == "grounded" and len(b.get("sources", [])) == 1,
    f"http={r.status_code} status={b.get('status')} sources={len(b.get('sources', []))}",
)

# 2. Invalid empty question
r = client.post("/api/ask", json={"question": "   "})
check("2 empty question rejected", r.status_code in (400, 422), f"http={r.status_code}")

# 3. Missing question field
r = client.post("/api/ask", json={})
check("3 missing question rejected", r.status_code in (400, 422), f"http={r.status_code}")

# 4. Unsupported question abstains
r = client.post("/api/ask", json={"question": "What is the maximum number of condonation applications a student can submit?"})
b = r.json()
check(
    "4 unsupported abstains",
    r.status_code == 200 and b.get("status") == "insufficient_evidence" and b.get("sources") == [],
    f"status={b.get('status')} sources={b.get('sources')}",
)

# 5. Unrelated topic, no fabrication
r = client.post("/api/ask", json={"question": "What is the library timing?"})
b = r.json()
check(
    "5 unrelated abstains, no fabricated source",
    r.status_code == 200 and b.get("status") == "insufficient_evidence" and b.get("sources") == [],
    f"status={b.get('status')} sources={b.get('sources')}",
)

# 6. Condition preservation
r = client.post("/api/ask", json={"question": "My attendance is 70%. Can I write the semester examination?"})
ans = r.json().get("answer", "")
check(
    "6 conditions preserved",
    all(x in ans for x in ("75%", "65-74%", "condonation", "approval")),
    "answer includes 75%, 65-74%, condonation, approval",
)

# 7. Health + frontend served
h = client.get("/health")
i = client.get("/")
check("7 health + frontend served", h.status_code == 200 and i.status_code == 200, f"health={h.status_code} index={i.status_code}")

# 8. Citation integrity
r = client.post("/api/ask", json={"question": "My attendance is 70%. Can I write the semester examination?"})
b = r.json()
src_ids = [s.get("chunk_id") for s in b.get("sources", [])]
check(
    "8 source chunk_id traceable to real L2 chunk",
    src_ids == ["attendance-policy-examination-eligibility-001"],
    f"source_chunk_ids={src_ids}",
)

print()
failed = [x for x in results if not x[1]]
print(f"TOTAL: {len(results) - len(failed)}/{len(results)} passed")
sys.exit(0 if not failed else 1)
