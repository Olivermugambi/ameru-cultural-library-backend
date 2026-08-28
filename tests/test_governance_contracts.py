from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parents[1]
ISSUE_TEMPLATES = ROOT / ".github" / "ISSUE_TEMPLATE"

IMPLEMENTATION_FIELDS = {
    "summary",
    "goal",
    "current-state",
    "expected-state",
    "constraints",
    "resolution-plan",
    "acceptance-criteria",
    "evidence-expectations",
    "stop-rules",
    "validation-criteria",
}
EPIC_FIELDS = IMPLEMENTATION_FIELDS | {
    "child-scopes",
    "shared-interfaces",
    "execution-order",
}


def load_form(name: str) -> dict[str, object]:
    with (ISSUE_TEMPLATES / name).open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def field_ids(form: dict[str, object]) -> set[str]:
    return {
        field["id"]
        for field in form["body"]
        if isinstance(field, dict) and isinstance(field.get("id"), str)
    }


def validate_form(form: dict[str, object], required_fields: set[str]) -> list[str]:
    errors: list[str] = []
    if not form.get("name"):
        errors.append("name is required")
    if not form.get("description"):
        errors.append("description is required")
    missing = required_fields - field_ids(form)
    if missing:
        errors.append(f"missing fields: {', '.join(sorted(missing))}")
    for field in form.get("body", []):
        if isinstance(field, dict) and field.get("id") in required_fields:
            attributes = field.get("attributes", {})
            if field.get("type") != "textarea":
                errors.append(f"{field['id']} must be a textarea")
            if not isinstance(attributes, dict) or not attributes.get("label"):
                errors.append(f"{field['id']} must have a label")
            validations = field.get("validations", {})
            if not isinstance(validations, dict) or validations.get("required") is not True:
                errors.append(f"{field['id']} must be required")
    return errors


@pytest.mark.parametrize(
    ("filename", "required_fields"),
    [
        ("implementation.yml", IMPLEMENTATION_FIELDS),
        ("epic.yml", EPIC_FIELDS),
    ],
)
def test_issue_forms_have_complete_required_contracts(
    filename: str, required_fields: set[str]
) -> None:
    assert validate_form(load_form(filename), required_fields) == []


def test_issue_form_validator_rejects_a_missing_required_field() -> None:
    form = load_form("implementation.yml")
    invalid = deepcopy(form)
    invalid["body"] = [field for field in invalid["body"] if field.get("id") != "stop-rules"]

    assert validate_form(invalid, IMPLEMENTATION_FIELDS) == ["missing fields: stop-rules"]


def test_issue_form_validator_rejects_a_malformed_required_field() -> None:
    form = load_form("implementation.yml")
    invalid = deepcopy(form)
    goal = next(field for field in invalid["body"] if field.get("id") == "goal")
    goal["type"] = "input"
    goal["attributes"].pop("label")

    assert validate_form(invalid, IMPLEMENTATION_FIELDS) == [
        "goal must be a textarea",
        "goal must have a label",
    ]


def test_acceptance_criteria_prompt_requires_markdown_checkboxes() -> None:
    for filename in ("implementation.yml", "epic.yml"):
        form = load_form(filename)
        acceptance = next(
            field for field in form["body"] if field.get("id") == "acceptance-criteria"
        )
        assert "- [ ]" in acceptance["attributes"]["placeholder"]


PR_SECTIONS = {
    "## Linked issue and workspace",
    "## Summary and goal",
    "## Work completed",
    "## Scope and constraints",
    "## Acceptance criteria",
    "## Automated validation",
    "## Manual evidence",
    "## Blockers and follow-ups",
    "## Final rebase and merge readiness",
}


def missing_pr_contracts(template: str) -> set[str]:
    required_statements = {
        "Dedicated worktree",
        "Dedicated branch",
        "Unchecked mandatory acceptance criteria block merge",
        "Every checked acceptance criterion links to evidence or validation",
        "Any remaining manual verification has a linked follow-up issue; otherwise, N/A",
        "Any out-of-scope blockers have a linked issue; otherwise, N/A",
        "Any blocking prerequisite stopped implementation; otherwise, N/A",
        "Rebased onto current `main`",
        "Complete validation rerun after the final rebase",
        "Rebase and merge",
    }
    return {contract for contract in PR_SECTIONS | required_statements if contract not in template}


def test_pull_request_template_has_complete_scope_and_evidence_contract() -> None:
    template = (ROOT / ".github" / "pull_request_template.md").read_text()

    assert missing_pr_contracts(template) == set()
    assert "- [ ]" in template


def test_pull_request_contract_rejects_missing_manual_evidence_disposition() -> None:
    template = (ROOT / ".github" / "pull_request_template.md").read_text()
    invalid = template.replace(
        "Any remaining manual verification has a linked follow-up issue; otherwise, N/A", ""
    )

    assert (
        "Any remaining manual verification has a linked follow-up issue; otherwise, N/A"
        in missing_pr_contracts(invalid)
    )


def test_contribution_policy_defines_review_enforcement_without_redefining_git() -> None:
    policy = " ".join((ROOT / "CONTRIBUTING.md").read_text().split())

    for statement in (
        "Issue and pull request contracts",
        "unchecked mandatory acceptance criterion blocks merge",
        "checkbox is a disposition, not evidence",
        "out-of-scope blocker",
        "remaining manual verification",
        "GIT_WORKFLOW.md",
    ):
        assert statement in policy
