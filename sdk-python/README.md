# Tracewell Python SDK

Python package that application developers will install to send AI agent observability data to Tracewell.

## Responsibilities

- Provide a small public Python API for recording traces.
- Capture prompts, responses, tool calls, latency, token usage, and errors.
- Send collected telemetry to the Tracewell backend.
- Keep instrumentation simple and framework-agnostic for the MVP.

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

The SDK currently exposes a minimal client placeholder. Transport and instrumentation will be implemented once the backend ingestion contract exists.
