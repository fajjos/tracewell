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
