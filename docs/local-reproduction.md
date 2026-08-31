# Docker local reproduction

This is the canonical clean-checkout path for running the backend and its full
verification gate locally. The current bootstrap is one FastAPI service and has
no database or other external runtime dependency.

## Prerequisites

- Docker Engine with Docker Compose v2 and support for `docker compose up --wait`.
- `curl` for host-side endpoint checks.
- Free local port 8000, or set `APP_PORT` to another free port.

All commands run from the backend repository root. Optional local overrides can
be created without committing them:

```bash
cp .env.example .env
```

Compose reads `.env` for interpolation. It passes only the explicitly declared
non-secret application settings into the container.

## Build and start

Validate the resolved configuration before contacting the container runtime:

```bash
docker compose config
docker compose build --no-cache
docker compose up --wait
docker compose ps
```

The runtime image uses a pinned Python patch/minimal-distribution tag, runs as
UID/GID 10001, drops Linux capabilities, prevents privilege escalation, and has
a read-only filesystem with only a temporary `/tmp` mount.

If port 8000 is already used:

```bash
APP_PORT=8080 docker compose up --wait
```

Use the same port in the manual requests below.

## Automated verification

The opt-in `tests` profile builds a separate test target and runs the same Ruff
and complete pytest gates used by CI. Their caches are disabled so the checks
remain compatible with the test container's read-only filesystem:

```bash
docker compose --profile test run --rm tests
```

Expected result: Ruff reports `All checks passed!` and pytest reports every
collected test passing. The test container does not publish a port or start as
part of the normal application topology.

## Manual verification

Record the command, response, container status, image/tree revision, and any
deviation from the expected result.

1. Health endpoint:

   ```bash
   curl --fail http://localhost:8000/health
   ```

   Expected JSON: `{"status":"ok"}`.

2. Versioned API root:

   ```bash
   curl --fail http://localhost:8000/api/v1
   ```

   Expected JSON: `{"version":"v1","status":"available"}`.

3. OpenAPI document:

   ```bash
   curl --fail http://localhost:8000/openapi.json
   ```

   Expected result: HTTP 200 and an OpenAPI document titled
   `Ameru Cultural Library API`.

4. Readiness:

   ```bash
   docker compose ps
   ```

   Expected result: the `app` service is `healthy`, not merely running.

## Logs and troubleshooting

```bash
docker compose logs app
docker compose ps
docker compose config
```

- Build failure: retain the failing build step and verify network access to the
  Python package index; do not remove dependency bounds to obtain a build.
- Unhealthy service: inspect `docker compose logs app` and confirm the health
  request reaches `/health`.
- Unexpected endpoint or stale image: record `git rev-parse HEAD`, then run
  `docker compose build --no-cache` and inspect the packaged route set with
  `docker compose run --rm --no-deps app python -c "from app.main import app; print(sorted(route.path for route in app.routes))"`.
- Port collision: choose an unused port with `APP_PORT`; do not edit the
  container's internal port.
- Configuration error: compare `docker compose config` with `.env.example` and
  remove undocumented overrides.

## Reset and teardown

Normal teardown removes only this Compose project's containers and network:

```bash
docker compose down --remove-orphans
```

The bootstrap declares no persistent volume. For a complete project-scoped
reset that also removes any volumes introduced later:

```bash
docker compose down --volumes --remove-orphans
```

After teardown, repeat `docker compose up --wait`, the automated verification,
and the health request. A second successful cycle proves that no undocumented
host state is required.
