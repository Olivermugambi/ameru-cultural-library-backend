from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

SOURCE_HELPER = Path(__file__).parents[1] / ".project-policy" / "worktree-lifecycle"


def git(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, check=check, text=True, capture_output=True)


@pytest.fixture
def repository(tmp_path: Path) -> tuple[Path, Path]:
    remote = tmp_path / "remote.git"
    base = tmp_path / "backend"
    git("init", "--bare", str(remote), cwd=tmp_path)
    git("init", "-b", "main", str(base), cwd=tmp_path)
    git("config", "user.email", "test@example.com", cwd=base)
    git("config", "user.name", "Test User", cwd=base)
    (base / "README.md").write_text("baseline\n")
    git("add", "README.md", cwd=base)
    git("commit", "-m", "initial", cwd=base)
    helper_path = base / ".project-policy" / "worktree-lifecycle"
    helper_path.parent.mkdir()
    shutil.copy2(SOURCE_HELPER, helper_path)
    helper_path.chmod(0o755)
    git("add", ".project-policy/worktree-lifecycle", cwd=base)
    git("commit", "-m", "add lifecycle helper", cwd=base)
    git("remote", "add", "origin", str(remote), cwd=base)
    git("push", "-u", "origin", "main", cwd=base)
    return base, remote


def helper(base: Path, *args: str) -> subprocess.CompletedProcess[str]:
    destination = base / ".project-policy" / "worktree-lifecycle"
    destination.parent.mkdir(exist_ok=True)
    shutil.copy2(SOURCE_HELPER, destination)
    destination.chmod(0o755)
    return subprocess.run([str(destination), *args], cwd=base, text=True, capture_output=True)


def test_create_uses_canonical_branch_and_sibling_location(
    repository: tuple[Path, Path],
) -> None:
    base, _ = repository

    result = helper(base, "create", "65", "worktree-branch-lifecycle", "p0")

    expected = base.parent / f"{base.name}-worktrees" / "issue-65"
    assert result.returncode == 0, result.stderr
    assert expected.is_dir()
    assert git("branch", "--show-current", cwd=expected).stdout.strip() == (
        "p0/65-worktree-branch-lifecycle"
    )
    assert str(expected) in git("worktree", "list", "--porcelain", cwd=base).stdout


@pytest.mark.parametrize("issue", ["0", "abc", "65/2"])
def test_create_rejects_invalid_issue_number(repository: tuple[Path, Path], issue: str) -> None:
    base, _ = repository
    result = helper(base, "create", issue, "slug", "p0")
    assert result.returncode != 0
    assert "positive integer" in result.stderr


def test_create_rejects_dirty_base(repository: tuple[Path, Path]) -> None:
    base, _ = repository
    (base / "README.md").write_text("dirty\n")
    result = helper(base, "create", "65", "slug", "p0")
    assert result.returncode != 0
    assert "dirty" in result.stderr.lower()


def test_create_rejects_base_not_on_main(repository: tuple[Path, Path]) -> None:
    base, _ = repository
    git("switch", "-c", "unrelated/branch", cwd=base)

    result = helper(base, "create", "65", "slug", "p0")

    assert result.returncode != 0
    assert "must be on main" in result.stderr


def test_create_rejects_base_not_equal_to_origin_main(
    repository: tuple[Path, Path],
) -> None:
    base, _ = repository
    (base / "local.txt").write_text("ahead\n")
    git("add", "local.txt", cwd=base)
    git("commit", "-m", "local ahead", cwd=base)
    result = helper(base, "create", "65", "slug", "p0")
    assert result.returncode != 0
    assert "origin/main" in result.stderr


def test_create_rejects_an_existing_branch_for_same_issue(
    repository: tuple[Path, Path],
) -> None:
    base, _ = repository
    git("branch", "p0/65-old-attempt", cwd=base)
    result = helper(base, "create", "65", "new-attempt", "p0")
    assert result.returncode != 0
    assert "already maps" in result.stderr


def test_create_rejects_pre_existing_target_path(repository: tuple[Path, Path]) -> None:
    base, _ = repository
    target = base.parent / f"{base.name}-worktrees" / "issue-65"
    target.mkdir(parents=True)
    marker = target / "preserve.txt"
    marker.write_text("do not overwrite\n")

    result = helper(base, "create", "65", "slug", "p0")

    assert result.returncode != 0
    assert "already exists" in result.stderr
    assert marker.read_text() == "do not overwrite\n"


def test_cleanup_rejects_dirty_worktree(repository: tuple[Path, Path]) -> None:
    base, _ = repository
    assert helper(base, "create", "65", "slug", "p0").returncode == 0
    worktree = base.parent / f"{base.name}-worktrees" / "issue-65"
    (worktree / "README.md").write_text("dirty\n")
    result = helper(base, "cleanup", "65")
    assert result.returncode != 0
    assert "uncommitted" in result.stderr
    assert worktree.exists()


def test_cleanup_rejects_unmerged_commit(repository: tuple[Path, Path]) -> None:
    base, _ = repository
    assert helper(base, "create", "65", "slug", "p0").returncode == 0
    worktree = base.parent / f"{base.name}-worktrees" / "issue-65"
    git("config", "user.email", "test@example.com", cwd=worktree)
    git("config", "user.name", "Test User", cwd=worktree)
    (worktree / "change.txt").write_text("change\n")
    git("add", "change.txt", cwd=worktree)
    git("commit", "-m", "unmerged", cwd=worktree)
    result = helper(base, "cleanup", "65")
    assert result.returncode != 0
    assert "not represented" in result.stderr
    assert worktree.exists()


def test_cleanup_rejects_branch_mapped_to_another_issue(
    repository: tuple[Path, Path],
) -> None:
    base, _ = repository
    assert helper(base, "create", "65", "slug", "p0").returncode == 0
    worktree = base.parent / f"{base.name}-worktrees" / "issue-65"
    git("branch", "-m", "p0/66-other-issue", cwd=worktree)

    result = helper(base, "cleanup", "65")

    assert result.returncode != 0
    assert "does not map" in result.stderr
    assert worktree.exists()
    assert git("branch", "--show-current", cwd=worktree).stdout.strip() == "p0/66-other-issue"


def test_cleanup_removes_only_clean_fully_integrated_work(
    repository: tuple[Path, Path], tmp_path: Path
) -> None:
    base, remote = repository
    assert helper(base, "create", "65", "slug", "p0").returncode == 0
    worktree = base.parent / f"{base.name}-worktrees" / "issue-65"
    git("config", "user.email", "test@example.com", cwd=worktree)
    git("config", "user.name", "Test User", cwd=worktree)
    (worktree / "change.txt").write_text("change\n")
    git("add", "change.txt", cwd=worktree)
    git("commit", "-m", "integrated", cwd=worktree)
    issue_commit = git("rev-parse", "HEAD", cwd=worktree).stdout.strip()
    integration = tmp_path / "integration"
    git("clone", "-b", "main", str(remote), str(integration), cwd=tmp_path)
    git("config", "user.email", "integrator@example.com", cwd=integration)
    git("config", "user.name", "Integrator", cwd=integration)
    git("fetch", str(base), "p0/65-slug", cwd=integration)
    git("cherry-pick", "FETCH_HEAD", cwd=integration)
    assert git("rev-parse", "HEAD", cwd=integration).stdout.strip() != issue_commit
    git("push", "origin", "main", cwd=integration)
    git("fetch", "origin", "main", cwd=base)

    result = helper(base, "cleanup", "65")

    assert result.returncode == 0, result.stderr
    assert not worktree.exists()
    assert "p0/65-slug" not in git("branch", "--format=%(refname:short)", cwd=base).stdout
    assert git("rev-parse", "origin/main", cwd=base).stdout
    assert remote.exists()


def test_compare_and_swap_ref_deletion_retains_a_branch_that_moved(
    repository: tuple[Path, Path],
) -> None:
    """Exercise the exact Git primitive cleanup uses after its safety proof."""
    base, _ = repository
    branch = "p0/65-race-proof"
    git("branch", branch, cwd=base)
    old_tip = git("rev-parse", branch, cwd=base).stdout.strip()
    git("switch", branch, cwd=base)
    (base / "moved.txt").write_text("new tip\n")
    git("add", "moved.txt", cwd=base)
    git("commit", "-m", "move branch after proof", cwd=base)
    moved_tip = git("rev-parse", branch, cwd=base).stdout.strip()

    deletion = git("update-ref", "-d", f"refs/heads/{branch}", old_tip, cwd=base, check=False)

    assert deletion.returncode != 0
    assert git("rev-parse", branch, cwd=base).stdout.strip() == moved_tip


def test_create_refuses_nested_location_override(repository: tuple[Path, Path]) -> None:
    base, _ = repository
    env = os.environ | {"WORKTREE_ROOT": str(base / "nested")}
    destination = base / ".project-policy" / "worktree-lifecycle"
    destination.parent.mkdir(exist_ok=True)
    shutil.copy2(SOURCE_HELPER, destination)
    destination.chmod(0o755)
    result = subprocess.run(
        [str(destination), "create", "65", "slug", "p0"],
        cwd=base,
        env=env,
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "inside" in result.stderr
