# Tracewell Backend

FastAPI service for receiving and querying AI agent observability data.

## Responsibilities

- Own the HTTP API surface for the Tracewell backend.
- Manage MongoDB connections through Motor.
- Validate request and response payloads with Pydantic v2 schemas.
- Coordinate business logic in service modules.
- Run rule-based failure detection over collected traces.

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Seed Demo Data

With MongoDB and the backend running:

```powershell
python scripts\seed_demo_traces.py
```

The script sends realistic traces through `POST /api/v1/traces`, including success, failure, high-latency, high-token, and repeated-tool-call examples.

## Environment Variables

Create a `.env` file from `.env.example`.

## Implemented Endpoints

- `GET /`
- `GET /health`
- `POST /api/v1/traces`
- `GET /api/v1/traces`
- `GET /api/v1/traces/{trace_id}`
- `POST /api/v1/evaluations/from-trace/{trace_id}`
- `GET /api/v1/evaluations`
- `GET /api/v1/evaluations/{evaluation_id}`
- `PATCH /api/v1/evaluations/{evaluation_id}`
- `POST /api/v1/evaluations/{evaluation_id}/runs`
- `GET /api/v1/evaluations/{evaluation_id}/runs`
- `GET /api/v1/evaluation-runs/{run_id}`

## Regression Testing MVP

Evaluations are deterministic regression tests created from stored traces. A developer creates an evaluation from a source trace, optionally edits its assertions, submits a new trace from a later agent run through the existing SDK, then runs the evaluation against that actual trace.

Create an evaluation:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/v1/evaluations/from-trace/{trace_id}
```

Run an evaluation against a second stored trace:

```powershell
Invoke-RestMethod -Method Post `
  -ContentType "application/json" `
  -Body '{"actual_trace_id":"trace_actual"}' `
  http://127.0.0.1:8000/api/v1/evaluations/{evaluation_id}/runs
```

Supported assertion types:

- `response_non_empty`
- `response_contains`
- `status_equals`
- `required_tool_called`
- `forbidden_tool_not_called`
- `max_tool_calls`
- `max_latency_ms`
- `max_tokens`

## Tests

Run backend tests from the `backend/` directory:

```powershell
python -m pytest
```

The evaluation tests use an in-memory fake database and do not require MongoDB credentials.
