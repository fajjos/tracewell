# Tracewell Python SDK

Python package that application developers will install to send AI agent observability data to Tracewell.

## Install

From this monorepo:

```bash
cd sdk-python
pip install -e .
```

## Quick Start

Start the Tracewell backend locally, then send a trace:

```python
from tracewell import Tracewell

client = Tracewell(api_key="demo")

client.trace(
    prompt="Hello",
    response="Hi",
    latency_ms=230,
)
```

By default, the SDK sends traces to:

```text
http://localhost:8000/api/v1/traces
```

## Configuration

You can configure the client directly:

```python
from tracewell import Tracewell

client = Tracewell(
    api_key="demo",
    base_url="http://localhost:8000",
    project_id="support-agent",
)
```

Or with environment variables:

```bash
export TRACEWELL_API_KEY=demo
export TRACEWELL_BASE_URL=http://localhost:8000
export TRACEWELL_PROJECT_ID=support-agent
```

## API

### `Tracewell(...)`

```python
Tracewell(
    api_key: str | None = None,
    base_url: str = "http://localhost:8000",
    project_id: str = "default",
    timeout: float = 5.0,
)
```

### `client.trace(...)`

```python
client.trace(
    prompt="Hello",
    response="Hi",
    latency_ms=230,
)
```

Optional fields:

```python
client.trace(
    prompt="Summarize this support ticket.",
    response="The customer needs billing help.",
    latency_ms=842,
    provider="openai",
    model="gpt-4.1-mini",
    input_tokens=32,
    output_tokens=18,
    cost=0.00014,
    status="success",
    tool_calls=[{"name": "search"}],
)
```

The method validates the payload, sends it to the backend, and returns:

```python
result.trace_id
```

## Examples

- `examples/simple_trace.py`
- `examples/advanced_trace.py`

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

## Notes

- The SDK is synchronous for the MVP.
- Authentication headers are included when `api_key` is provided, but the MVP backend does not enforce authentication.
- `trace_id` and `session_id` are generated automatically unless passed explicitly.
- `project_id` defaults to `TRACEWELL_PROJECT_ID` or `default`.
