from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "ci.yml"
REQUIRED_STEP_NAMES = [
    "Checkout",
    "Set up Python",
    "Install dependencies",
    "Verify package",
    "Ruff",
    "Shell syntax",
    "Repository boundary",
    "Full test suite",
]


def load_workflow() -> dict[str, Any]:
    with WORKFLOW_PATH.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def workflow_triggers(workflow: dict[str, Any]) -> dict[str, Any]:
    # PyYAML 1.1 treats the unquoted YAML key `on` as boolean true.
    return workflow.get("on", workflow.get(True, {}))


def required_job(workflow: dict[str, Any]) -> dict[str, Any]:
    return workflow["jobs"]["verify"]


def step_by_name(job: dict[str, Any], name: str) -> dict[str, Any]:
    return next(step for step in job["steps"] if step.get("name") == name)


def test_ci_runs_for_pull_requests_and_main_pushes() -> None:
    triggers = workflow_triggers(load_workflow())

    assert "pull_request" in triggers
    assert triggers["push"]["branches"] == ["main"]


def test_required_check_name_permissions_and_concurrency_are_stable() -> None:
    workflow = load_workflow()
    job = required_job(workflow)

    assert workflow["name"] == "CI"
    assert job["name"] == "P0 required checks"
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["concurrency"] == {
        "group": "${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}",
        "cancel-in-progress": True,
    }


def test_required_job_contains_every_blocking_gate_in_order() -> None:
    job = required_job(load_workflow())

    assert [step.get("name") for step in job["steps"]] == REQUIRED_STEP_NAMES
    assert job["runs-on"] == "ubuntu-latest"

    install = step_by_name(job, "Install dependencies")["run"]
    assert "python -m pip install -e '.[dev]'" in install
    assert "python -m pip check" in install

    package = step_by_name(job, "Verify package")["run"]
    assert "python -m pip wheel --no-deps" in package
    assert 'python -c "import app.main"' in package

    assert step_by_name(job, "Ruff")["run"] == "python -m ruff check ."
    assert step_by_name(job, "Shell syntax")["run"] == (
        "bash -n .project-policy/git-guard .project-policy/install.sh .githooks/pre-push"
    )
    assert step_by_name(job, "Repository boundary")["run"] == (
        "python -m pytest tests/test_repository_boundary.py"
    )
    assert step_by_name(job, "Full test suite")["run"] == "python -m pytest"


def test_required_job_has_no_non_blocking_escape_hatch() -> None:
    job = required_job(load_workflow())

    assert "continue-on-error" not in job
    assert all("continue-on-error" not in step for step in job["steps"])
    assert all("if" not in step for step in job["steps"])


def test_checkout_does_not_persist_write_credentials() -> None:
    checkout = step_by_name(required_job(load_workflow()), "Checkout")

    assert checkout["uses"] == "actions/checkout@v4"
    assert checkout["with"] == {"persist-credentials": False}
