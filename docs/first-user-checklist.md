# First User Checklist

Use this checklist before showing Tracewell to a developer.

## Before The Call

- Pull the latest `main` branch.
- Start MongoDB locally.
- Start the FastAPI backend.
- Start the React frontend.
- Run `python scripts\seed_demo_traces.py` from the `backend` folder.
- Confirm the dashboard shows traces and failure signals.
- Confirm the SDK sends a trace into the dashboard.

## Demo Flow

1. Open the dashboard and show total traces, failures, latency, and spend.
2. Open the traces page and show filtering by status or project.
3. Open a failed trace and show prompt, response, latency, token usage, tool calls, and the trace viewer.
4. Run the Python SDK example live and refresh the dashboard.
5. Explain that Tracewell is intentionally local-first and MVP-focused.

## Questions To Ask

- What AI agent or LLM workflow would you want to observe first?
- What is hardest to debug today: prompts, tools, latency, costs, or failures?
- Would this SDK be simple enough to add to your current project?
- What information is missing from the trace details page?
- Would you use this locally before production?

## Success Criteria

- The user understands the SDK-to-dashboard flow in under five minutes.
- The user can name one real workflow where Tracewell would help.
- The user gives at least one concrete missing feature or confusing part.
- The demo does not require authentication, billing, or infrastructure setup beyond local MongoDB.
