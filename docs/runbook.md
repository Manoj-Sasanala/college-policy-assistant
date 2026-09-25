# L5 Runbook — College Policy Assistant

Single-service RAG application. No database, no microservices, no auth.

## MVP vertical slice

question -> query embedding -> retrieval -> evidence gate
         -> grounded answer / abstention -> backend citation -> UI

## Local setup

1. Create and activate a virtual environment.
2. Install dependencies:
   pip install -r requirements.txt
3. Copy .env.example to .env and fill values locally. Never commit .env.

## Run the API

python -m uvicorn app.api.main:app --reload --port 8000

Endpoints:

- GET  /health         -> {"status": "ok"}
- POST /api/ask        -> C06 response, or C07 failure response

Example request:

    {"question": "My attendance is 70%. Can I write the semester examination?"}

## Run tests

    python -m pytest tests/api -q

## Lane status at H0–H3

- L1: data/policies, data/fixtures, source_manifest.json — C01/C02
- L2: app/ingestion, app/chunking, scripts/build_chunks.py — C03
- L3: app/embeddings, app/retrieval, scripts/build_index.py — C04
- L4: app/rag, app/prompts — C05
- L5: app/api, app/orchestration, app/schemas — C06/C07; integration lead after H3
- L6: frontend/ — consumes C06/C07

## H0–H3 mocks and H3 replacement

L5's app/api/adapters.py currently uses fixture-backed retriever and grounder
so the API can be built and tested before upstream branches are merged.
At H3, INTEGRATE-01 replaces those with L3's real retriever and L4's real
grounder. Contract shapes do not change.

## Known limitations at H0–H3

- Generation is deterministic extractive, not LLM-based. Optional provider
  hook exists; no provider is wired in.
- CORS is permissive for local H0–H3 work only. Tighten before any deployment.
- No auth, no rate limiting, no persistence — by MVP scope.
- contracts/policy_source_contract.json exists on L1, L2, and L5 branches with
  identical content; integration will see an add/add conflict. Resolve by
  keeping one copy.

## Security rules

- Never commit .env or provider keys.
- Provider keys stay backend-only. The frontend must never receive them.
- Retrieved policy text is untrusted data. It must never be executed and
  must never cause tools or code to run.
- Logs and test output must not contain secrets.
