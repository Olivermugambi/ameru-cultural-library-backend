# Ameru Cultural Library Backend

The authoritative content and API layer for the Ameru Cultural Library. This FastAPI service serves culturally structured books, artifacts, programs, learning material, Explore content, and Baraza material to the Next.js frontend.

## Role
The frontend owns presentation and interaction. This service owns content contracts, validation, relationships, provenance/status semantics, media metadata, and the persistence boundary.

## Principles
- Treat the cultural record as structured knowledge, not page-local copy.
- Distinguish source material, editorial interpretation, contemporary contribution, and speculation.
- Preserve provenance and attribution rather than manufacturing authority.
- Keep media semantics explicit (`cover`, `contain`, `gallery`).
- Version the API under `/api/v1`.
- Keep domain logic independent of FastAPI and persistence implementation.
- Prefer small, composable contracts over premature CMS infrastructure.

## Development
Use Python 3.12+ and a virtual environment. The initial scaffold uses deterministic in-memory fixtures; persistence is introduced behind repository interfaces.

```bash
pip install -e '.[dev]'
pytest
uvicorn app.main:app --reload
```

API docs are available at `/docs` and `/openapi.json` when running locally.

## Repository boundaries
This repository is not the frontend, CMS, authentication system, moderation platform, or archival ingestion pipeline. See `ARCHITECTURE.md`, `DOMAIN_MODEL.md`, and `CONTENT_GOVERNANCE.md` before extending it.