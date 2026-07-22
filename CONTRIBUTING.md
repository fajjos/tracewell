# Contributing to Tracewell

Tracewell is in early MVP development. Contributions should keep the product simple, focused, and useful for developers building AI agents.

## Principles

- Prefer small, reviewable changes.
- Keep the MVP free of enterprise features until the core workflow works.
- Use clear type hints and explicit boundaries between routes, schemas, models, and services.
- Avoid adding infrastructure unless it directly supports the MVP.
- Update documentation when behavior or setup changes.

## Local Development

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

SDK:

```bash
cd sdk-python
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Commit Style

Use Conventional Commits:

```text
feat: add trace ingestion endpoint
fix: handle missing trace duration
docs: document local setup
chore: update repository metadata
```

## Pull Request Checklist

- The change is scoped to one clear concern.
- Application code includes type hints where applicable.
- New behavior is documented.
- Tests or verification notes are included when relevant.
- No secrets, local `.env` files, virtual environments, or dependency folders are committed.
