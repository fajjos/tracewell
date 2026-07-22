# Tracewell MVP Architecture

## Backend

The backend is a FastAPI application organized around explicit boundaries:

- `api/`: HTTP route modules. Empty for now because product APIs are intentionally not implemented yet.
- `core/`: cross-cutting application concerns such as logging, constants, and error helpers.
- `database/`: MongoDB client lifecycle and collection access.
- `models/`: persistence-oriented database models.
- `schemas/`: Pydantic request and response schemas.
- `services/`: business logic that routes can call, including rule-based failure detection.
- `utils/`: small shared helpers that do not belong to a domain service.
- `config.py`: environment-driven application settings.
- `main.py`: FastAPI app factory and application lifecycle.

## Frontend

The frontend is a Vite React application using TailwindCSS and React Router. It starts with one placeholder route so the project can compile while the product screens are still being designed.

Recommended future folders:

- `src/pages/`: route-level screens.
- `src/components/`: reusable UI components.
- `src/lib/`: API clients and shared browser utilities.
- `src/types/`: TypeScript types shared across views.

## Python SDK

The SDK is a standalone Python package under `sdk-python/`. It exposes the public package namespace and a placeholder client. Actual telemetry capture should be added after the backend ingestion schema is designed.
