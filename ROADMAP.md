# Tracewell Roadmap

Tracewell is currently focused on proving the core AI agent observability loop.

## MVP Milestones

1. Repository foundation
   - Professional monorepo layout.
   - Backend, frontend, SDK, and docs packages.
   - Contribution, changelog, roadmap, and license files.

2. Trace ingestion contract
   - Define Pydantic schemas for traces, spans, prompts, responses, tool calls, token usage, latency, and errors.
   - Document the initial SDK-to-backend payload format.

3. Backend ingestion API
   - Add FastAPI routes for accepting traces.
   - Persist trace documents in MongoDB with Motor.
   - Return clear validation errors for malformed payloads.

4. Python SDK capture API
   - Add a small developer-facing client.
   - Capture latency and errors around traced operations.
   - Send trace payloads to the backend.

5. Rule-based failure detection
   - Detect errors, high latency, empty responses, failed tool calls, and token spikes.
   - Store failure signals alongside traces.

6. Developer dashboard
   - Add trace list, trace detail, prompt and response panels, tool call view, latency view, and failure badges.

7. Local developer experience
   - Improve setup docs.
   - Add example instrumented agent.
   - Add minimal tests for backend services and SDK behavior.

## First 10 GitHub Issues

1. Define the initial trace ingestion schema.
2. Add FastAPI route module for trace ingestion.
3. Implement MongoDB repository helpers for trace persistence.
4. Add backend service for creating traces and running failure detection.
5. Implement Python SDK client transport with `httpx`.
6. Add SDK context manager for tracing agent runs.
7. Build frontend trace list page.
8. Build frontend trace detail page with prompt, response, and tool call sections.
9. Add rule-based detection for runtime errors, high latency, empty responses, and failed tool calls.
10. Add an example Python agent app that sends traces to a local Tracewell backend.

## Suggested Milestone Commit Messages

```text
chore: scaffold tracewell monorepo
docs: add repository contribution and roadmap docs
feat(backend): define trace ingestion schemas
feat(backend): add trace ingestion endpoint
feat(backend): persist traces in mongodb
feat(sdk): add tracewell client transport
feat(sdk): add tracing context manager
feat(frontend): add dashboard shell and routing
feat(frontend): add trace list view
feat(frontend): add trace detail view
feat(backend): add rule-based failure detection
docs: add local example agent
```

## Later Roadmap

- Trace search and filtering.
- Prompt and response diffing.
- Better token and latency charts.
- React Flow trace graph visualization.
- Framework integrations for popular agent libraries.
- Hosted deployment path after the local MVP is useful.
