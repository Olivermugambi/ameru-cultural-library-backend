# Development

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Run the service:

```bash
uvicorn app.main:app --reload
```

Run checks:

```bash
pytest
ruff check .
```

## Implementation order
1. Approve domain and API contracts.
2. Add deterministic fixtures only where needed for UI integration.
3. Implement repository interfaces and service logic.
4. Expose validated API routes.
5. Add contract/domain/API tests.
6. Only then introduce persistence or external integrations.

## Stop conditions
Stop rather than inventing data when a required cultural fact is unknown. Stop before changing a public API shape if the frontend contract has already been consumed. Stop before adding infrastructure that is not required by an accepted feature.
