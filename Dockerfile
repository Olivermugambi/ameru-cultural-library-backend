# syntax=docker/dockerfile:1

FROM python:3.12.11-slim-bookworm AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build
COPY pyproject.toml README.md ./
COPY app ./app
RUN python -m pip wheel --wheel-dir /wheels .

FROM python:3.12.11-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels
RUN python -c "from app.main import app; paths = {route.path for route in app.routes}; assert {'/health', '/api/v1', '/openapi.json'} <= paths"

WORKDIR /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM builder AS test

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app \
    && python -m pip install --no-cache-dir -e '.[dev]'
COPY .github ./.github
COPY .project-policy ./.project-policy
COPY .githooks ./.githooks
COPY docs ./docs
COPY tests ./tests
COPY .env.example ./
COPY .dockerignore ./
COPY compose.yaml ./
COPY CONTRIBUTING.md ./
COPY DEVELOPMENT.md ./
COPY GIT_WORKFLOW.md ./
COPY AGENTS.md ./
USER app
CMD ["python", "-m", "pytest", "-p", "no:cacheprovider", "-q"]
