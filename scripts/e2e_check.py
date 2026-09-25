import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
from app.chunking.chunker import chunk_source
from app.ingestion.source_validator import validate_source
from app.rag.grounding import answer_from_retrieval
from app.retrieval.retriever import Retriever

c01 = json.loads(Path("data/fixtures/c01_attendance_policy.json").read_text(encoding="utf-8"))
validated = validate_source(c01)
print("STEP1 validated:", validated["document_id"])

chunks = chunk_source(validated)
print("STEP2 chunks:", len(chunks))
for c in chunks:
    print("  chunk_id:", c["chunk_id"])

retriever = Retriever(chunks)
query = "My attendance is 70%. Can I write the semester examination?"
c04 = retriever.retrieve(query, top_k=3, relevance_threshold=0.0)
print("STEP3 status:", c04["retrieval_status"], "results:", len(c04["results"]))
if c04["results"]:
    print("  top score:", c04["results"][0]["score"])

c05 = answer_from_retrieval(c04)
print("STEP4 status:", c05["status"])
print("STEP4 source_chunk_ids:", c05["source_chunk_ids"])
print("STEP4 answer:", c05["answer"][:200])

ok = (
    c05["status"] == "grounded"
    and c05["source_chunk_ids"] == [chunks[0]["chunk_id"]]
    and "75%" in c05["answer"]
    and "condonation" in c05["answer"]
)
print("END-TO-END:", "PASS" if ok else "FAIL")
