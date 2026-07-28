# Tracewell Local Demo

Use this guide to run Tracewell locally and show the full MVP loop to a first user.

## What This Demo Proves

- A developer can send traces through the Python SDK or HTTP API.
- FastAPI validates and stores traces in MongoDB.
- Rule-based failure detection identifies useful issues.
- The React dashboard shows traces, metrics, failures, and trace details.

## Prerequisites

- Python 3.9 or newer
- Node.js 18 or newer
- MongoDB running locally on `mongodb://localhost:27017`

## 1. Start MongoDB

Use your local MongoDB install. The backend defaults to:

```text
mongodb://localhost:27017
```

## 2. Start The Backend

```powershell
cd C:\Users\FAJJOS\OneDrive\Desktop\tracewell\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Check that the API is alive:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected response:

```text
healthy
-------
True
```

## 3. Start The Frontend

Open a second PowerShell terminal:

```powershell
cd C:\Users\FAJJOS\OneDrive\Desktop\tracewell\frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## 4. Seed Demo Traces

Open a third PowerShell terminal:

```powershell
cd C:\Users\FAJJOS\OneDrive\Desktop\tracewell\backend
python scripts\seed_demo_traces.py
```

The script sends five traces through the public API:

- successful trace
- failed response trace
- high latency trace
- high token usage trace
- repeated tool-call trace

Refresh the dashboard. You should see totals, failures, latency, spend, recent traces, and failure signals.

## 5. Test The Python SDK

Open a fourth PowerShell terminal:

```powershell
cd C:\Users\FAJJOS\OneDrive\Desktop\tracewell\sdk-python
python -m pip install -e .
```

Send a trace:

```powershell
python -c "from tracewell import Tracewell; client = Tracewell(api_key='demo', base_url='http://127.0.0.1:8000', project_id='first-user-demo'); result = client.trace(prompt='SDK first user demo', response='Tracewell received this trace from the Python SDK.', latency_ms=420, input_tokens=20, output_tokens=30, cost=0.0003); print(result.trace_id)"
```

Refresh the dashboard again. You should see a new `first-user-demo` trace.

## Demo Talk Track

Tracewell gives AI developers one place to inspect agent runs. The SDK sends prompts, responses, tool calls, latency, token usage, cost, and status to the backend. The dashboard makes those traces searchable and highlights failures with simple rules before any AI-based analysis is added.

## Troubleshooting

If the dashboard is empty, seed traces again and refresh the browser.

If seeding fails with a connection error, make sure the backend is running on `http://127.0.0.1:8000`.

If the backend fails on startup, make sure MongoDB is running locally.
