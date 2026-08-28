from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]


def load_compose() -> dict[str, object]:
    return yaml.safe_load((ROOT / "compose.yaml").read_text())


def compose_errors(config: dict[str, object]) -> list[str]:
    errors: list[str] = []
    services = config.get("services", {})
    if set(services) != {"app", "tests"}:
        errors.append("topology must contain only app and tests services")
        return errors

    app = services["app"]
    tests = services["tests"]
    if app.get("build", {}).get("target") != "runtime":
        errors.append("app must build the runtime target")
    if tests.get("build", {}).get("target") != "test":
        errors.append("tests must build the test target")
    if tests.get("profiles") != ["test"]:
        errors.append("tests service must be opt-in")
    test_command = " ".join(tests.get("command", []))
    if "ruff check --no-cache" not in test_command:
        errors.append("read-only tests must disable the Ruff cache")
    if "pytest -p no:cacheprovider" not in test_command:
        errors.append("read-only tests must disable the pytest cache")
    if app.get("ports") != ["${APP_PORT:-8000}:8000"]:
        errors.append("app port contract is missing")
    healthcheck = app.get("healthcheck", {})
    if "/health" not in " ".join(healthcheck.get("test", [])):
        errors.append("app health check must call /health")
    for name, service in services.items():
        if service.get("privileged"):
            errors.append(f"{name} must not be privileged")
        if service.get("read_only") is not True:
            errors.append(f"{name} filesystem must be read-only")
        if service.get("cap_drop") != ["ALL"]:
            errors.append(f"{name} must drop all capabilities")
        if "no-new-privileges:true" not in service.get("security_opt", []):
            errors.append(f"{name} must prohibit privilege escalation")
    return errors


def test_compose_defines_minimal_least_privilege_runtime_and_test_topology() -> None:
    assert compose_errors(load_compose()) == []


def test_compose_contract_rejects_privileged_runtime() -> None:
    invalid = deepcopy(load_compose())
    invalid["services"]["app"]["privileged"] = True

    assert "app must not be privileged" in compose_errors(invalid)


def test_dockerfile_pins_python_and_runs_runtime_as_non_root() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text()

    assert "FROM python:3.12.11-slim-bookworm AS builder" in dockerfile
    assert "FROM python:3.12.11-slim-bookworm AS runtime" in dockerfile
    assert "FROM builder AS test" in dockerfile
    assert "USER app" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert 'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]' in dockerfile
    assert "assert {'/health', '/api/v1', '/openapi.json'} <= paths" in dockerfile
    assert "COPY . ." not in dockerfile


def test_test_image_contains_complete_repository_contract_surface() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text()

    for source in (
        ".github",
        ".project-policy",
        ".githooks",
        "docs",
        "tests",
        ".env.example",
        ".dockerignore",
        "compose.yaml",
        "CONTRIBUTING.md",
        "DEVELOPMENT.md",
        "GIT_WORKFLOW.md",
        "AGENTS.md",
    ):
        assert f"COPY {source}" in dockerfile
    assert "apt-get install -y --no-install-recommends git" in dockerfile


def test_docker_context_excludes_local_and_repository_state() -> None:
    ignored = set((ROOT / ".dockerignore").read_text().splitlines())

    assert {".git", ".env", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"} <= ignored
    assert {".github", ".project-policy", ".githooks"}.isdisjoint(ignored)


def test_example_environment_contains_no_assigned_secret() -> None:
    for raw_line in (ROOT / ".env.example").read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if any(marker in key.upper() for marker in ("SECRET", "TOKEN", "PASSWORD", "KEY")):
            assert value == ""


def test_local_reproduction_guide_covers_complete_operator_lifecycle() -> None:
    guide = (ROOT / "docs" / "local-reproduction.md").read_text()

    for command in (
        "docker compose config",
        "docker compose build --no-cache",
        "docker compose up --wait",
        "curl --fail http://localhost:8000/health",
        "docker compose --profile test run --rm tests",
        "docker compose logs app",
        "docker compose down --remove-orphans",
        "docker compose down --volumes --remove-orphans",
    ):
        assert command in guide
    for heading in (
        "## Prerequisites",
        "## Build and start",
        "## Automated verification",
        "## Manual verification",
        "## Logs and troubleshooting",
        "## Reset and teardown",
    ):
        assert heading in guide


def test_readme_and_development_guide_link_to_canonical_docker_guide() -> None:
    for document in ("README.md", "DEVELOPMENT.md"):
        assert "docs/local-reproduction.md" in (ROOT / document).read_text()
