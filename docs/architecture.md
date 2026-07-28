# Tracewell MVP Architecture

## Backend

The backend is a FastAPI application organized around explicit boundaries:

- `api/`: HTTP route modules for health checks and trace resources.
- `core/`: cross-cutting application concerns such as logging, constants, and error helpers.
- `database/`: MongoDB client lifecycle and collection access.
- `models/`: persistence-oriented database models.
- `schemas/`: Pydantic request and response schemas.
- `services/`: business logic that routes can call, including rule-based failure detection.
- `utils/`: small shared helpers that do not belong to a domain service.
- `config.py`: environment-driven application settings.
- `main.py`: FastAPI app factory and application lifecycle.

The trace ingestion path is intentionally simple:

```text
SDK or HTTP client -> FastAPI route -> Pydantic schema -> service -> MongoDB
```

Failure detection runs in the service layer before the API response is returned. The current rules are deterministic and easy to extend.

## Frontend

The frontend is a Vite React application using TailwindCSS and React Router. It reads traces from the FastAPI backend and renders the dashboard, trace list, trace detail view, and React Flow trace viewer.

Key folders:

- `src/pages/`: route-level screens.
- `src/components/`: reusable UI components.
- `src/lib/`: API clients and shared browser utilities.

## Python SDK

The SDK is a standalone Python package under `sdk-python/`. It exposes `Tracewell`, validates trace payloads with Pydantic, and sends traces to the backend with a small synchronous API for the MVP.

## Local Demo

The repository includes `backend/scripts/seed_demo_traces.py` and [Local Demo](./local-demo.md) so a new user can validate the full product loop without having a real AI agent yet.
