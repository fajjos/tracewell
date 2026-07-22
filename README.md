# Tracewell

Tracewell is an open-source observability platform for AI agents.

The MVP helps developers understand what their agents are doing by collecting traces, prompts, responses, tool calls, latency, token usage, and errors through a lightweight Python SDK.

## Vision

AI agents are becoming production software, but debugging them still feels like reading scattered logs. Tracewell aims to give developers a focused, beautiful, local-first observability workflow for agent behavior before adding enterprise complexity.

The first version is intentionally small: one SDK, one API, one database, one dashboard, and practical rule-based failure detection.

## MVP Roadmap

- Python SDK
- FastAPI backend
- React frontend
- MongoDB persistence
- Rule-based failure detection
- Clean local developer experience

## Tech Stack

- Frontend: React, Vite, TailwindCSS, React Router
- Backend: FastAPI, Python 3.12, Pydantic v2, Motor, Uvicorn
- Database: MongoDB
- SDK: Python package

## Folder Structure

```text
tracewell/
|-- backend/
|   |-- app/
|   |   |-- api/        HTTP route modules
|   |   |-- core/       Cross-cutting application concerns
|   |   |-- database/   MongoDB client and collection access
|   |   |-- models/     Persistence models
|   |   |-- schemas/    Pydantic request and response schemas
|   |   |-- services/   Business logic and failure detection
|   |   |-- utils/      Shared utility functions
|   |   |-- config.py   Environment-driven settings
|   |   `-- main.py     FastAPI app factory
|   |-- requirements.txt
|   `-- README.md
|-- frontend/          React dashboard application
|-- sdk-python/        Python SDK package
|-- docs/              Architecture and development notes
|-- CONTRIBUTING.md
|-- ROADMAP.md
|-- CHANGELOG.md
|-- LICENSE
`-- README.md
```

## Local Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

On Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

On Windows PowerShell:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

### Python SDK

```bash
cd sdk-python
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

On Windows PowerShell:

```powershell
cd sdk-python
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## Current Development Status

Tracewell is pre-alpha. The repository is scaffolded for the MVP, but ingestion APIs, SDK transport, trace persistence, and dashboard views are not implemented yet.

Current scope:

- Monorepo structure is in place.
- Backend application shell is in place.
- Frontend application shell is in place.
- Python SDK package shell is in place.
- Product APIs are intentionally not implemented yet.

## Future Roadmap

- Define trace ingestion schemas.
- Implement backend ingestion endpoints.
- Persist trace data in MongoDB.
- Add SDK trace capture and transport.
- Build dashboard views for traces, spans, prompts, responses, tool calls, and failures.
- Add rule-based failure detection.
- Add developer documentation and examples.

## Package Documentation

- [Backend](./backend/README.md)
- [Frontend](./frontend/README.md)
- [Python SDK](./sdk-python/README.md)

## GitHub Topics

Suggested repository topics:

`ai-agents`, `observability`, `llmops`, `tracing`, `fastapi`, `react`, `vite`, `tailwindcss`, `mongodb`, `python-sdk`, `developer-tools`, `open-source`, `agent-debugging`

## License

MIT License. See [LICENSE](./LICENSE).
