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

## Environment Variables

Create a `.env` file from `.env.example`.

No product APIs are implemented yet. This package currently contains only the application structure and shared infrastructure placeholders.
