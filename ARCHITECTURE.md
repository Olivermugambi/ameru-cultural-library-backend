# Architecture

## System role

```text
Next.js frontend
      │ HTTPS / JSON
      ▼
FastAPI API (/api/v1)
      │
      ├── schemas: transport contracts
      ├── services: use-case/domain orchestration
      ├── repositories: persistence boundary
      └── domain: framework-independent models/rules
               │
               ▼
          persistence
```

The API is the authoritative runtime boundary for content consumed by the frontend. The frontend must not become a shadow database of cultural content.

## Layer rules
- `domain/` contains semantic models and rules; it must not import FastAPI.
- `schemas/` contains API representations and validation.
- `repositories/` abstracts storage and retrieval.
- `services/` coordinates use cases and relationships.
- `api/` maps HTTP requests to services and schemas.
- `main.py` only assembles the application.

## API
All public endpoints are versioned under `/api/v1`. OpenAPI is generated from the FastAPI application.

## Persistence
The initial implementation uses deterministic fixtures behind repository interfaces. Do not couple API handlers directly to an ORM. A database may be introduced later without changing API semantics.

## Frontend integration
The frontend project is `Olivermugambi/ameru-cultural-library`. Its feature work must consume these contracts rather than inventing parallel content models.

## Explicit non-goals
No CMS, authentication, moderation platform, recommendation engine, payment system, or archival-ingestion pipeline is part of the bootstrap.
