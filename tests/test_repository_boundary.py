from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
GUARD = ROOT / ".project-policy" / "git-guard"
INSTALL = ROOT / ".project-policy" / "install.sh"
PRE_PUSH = ROOT / ".githooks" / "pre-push"
BACKEND = "https://github.com/Olivermugambi/ameru-cultural-library-backend.git"
FRONTEND = "https://github.com/Olivermugambi/ameru-cultural-library.git"
THIRD = "https://github.com/Olivermugambi/not-authorized.git"


def run(
    *args: str, cwd: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def init_repo(path: Path, origin: str = BACKEND) -> None:
    path.mkdir()
    subprocess.run(["git", "init", "-q", path], check=True)
    subprocess.run(["git", "-C", path, "remote", "add", "origin", origin], check=True)


def transport_sentinel(tmp_path: Path) -> tuple[dict[str, str], Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    marker = tmp_path / "transport-contacted"
    transport = bin_dir / "git-remote-https"
    transport.write_text(f"#!/bin/sh\ntouch '{marker}'\nexit 99\n")
    transport.chmod(transport.stat().st_mode | stat.S_IXUSR)
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    return env, marker


def inert_git(tmp_path: Path) -> dict[str, str]:
    bin_dir = tmp_path / "inert-bin"
    bin_dir.mkdir()
    git = bin_dir / "git"
    git.write_text("#!/bin/sh\nexit 0\n")
    git.chmod(git.stat().st_mode | stat.S_IXUSR)
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    return env


def inert_remote_git(tmp_path: Path) -> dict[str, str]:
    env = inert_git(tmp_path)
    real_git = subprocess.run(
        ["which", "git"], text=True, capture_output=True, check=True
    ).stdout.strip()
    fake_git = Path(env["PATH"].split(":", 1)[0]) / "git"
    fake_git.write_text(
        f'#!/bin/sh\ncase "$1" in config|remote) exec \'{real_git}\' "$@" ;; esac\nexit 0\n'
    )
    return env


@pytest.mark.parametrize(
    "url",
    [
        BACKEND,
        BACKEND.removesuffix(".git"),
        f"{BACKEND}/",
        "git@github.com:Olivermugambi/ameru-cultural-library-backend.git",
        "ssh://git@github.com/Olivermugambi/ameru-cultural-library-backend/",
        FRONTEND,
        FRONTEND.removesuffix(".git"),
        "git@github.com:Olivermugambi/ameru-cultural-library.git",
        "ssh://git@github.com/Olivermugambi/ameru-cultural-library.git",
    ],
)
def test_clone_accepts_only_normalized_allowlist_urls(tmp_path: Path, url: str) -> None:
    result = run(
        GUARD, "clone", "--no-checkout", url, "checkout", cwd=tmp_path, env=inert_git(tmp_path)
    )

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "command",
    [
        ("clone", "--branch", "main", THIRD),
        ("fetch", THIRD),
        ("pull", THIRD, "main"),
        ("push", THIRD, "HEAD"),
        ("ls-remote", THIRD),
        ("remote", "add", "other", THIRD),
        ("remote", "set-url", "origin", THIRD),
        ("submodule", "add", THIRD, "vendor/third"),
    ],
)
def test_third_repository_is_rejected_before_transport(
    tmp_path: Path, command: tuple[str, ...]
) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    env, marker = transport_sentinel(tmp_path)

    result = run(GUARD, *command, cwd=repo, env=env)

    assert result.returncode == 77
    assert "PROJECT POLICY" in result.stderr
    assert not marker.exists()


@pytest.mark.parametrize("target_kind", ["absolute", "relative", "scp"])
@pytest.mark.parametrize("operation", ["fetch", "pull", "push", "ls-remote"])
def test_non_url_repository_targets_are_rejected(
    tmp_path: Path, target_kind: str, operation: str
) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    source = tmp_path / "local-source"
    subprocess.run(["git", "init", "-q", "--bare", source], check=True)
    targets = {
        "absolute": str(source),
        "relative": "../local-source",
        "scp": "other@github.com:Olivermugambi/not-authorized.git",
    }

    result = run(GUARD, operation, targets[target_kind], cwd=repo)

    assert result.returncode == 77


@pytest.mark.parametrize(
    "target",
    ["{absolute}", "../local-source", "other@github.com:Olivermugambi/not-authorized.git"],
)
def test_submodule_add_rejects_non_allowlist_target(tmp_path: Path, target: str) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    source = tmp_path / "local-source"
    subprocess.run(["git", "init", "-q", "--bare", source], check=True)
    resolved_target = str(source) if target == "{absolute}" else target

    result = run(GUARD, "submodule", "add", resolved_target, "vendor/x", cwd=repo)

    assert result.returncode == 77
    assert not (repo / "vendor" / "x").exists()


@pytest.mark.parametrize(
    "command",
    [
        ("fetch", "--depth", "1", "origin", "main"),
        ("pull", "--rebase", "origin", "main"),
        ("push", "--set-upstream", "origin", "HEAD"),
        ("ls-remote", "--heads", "origin", "main"),
    ],
)
def test_origin_target_preserves_following_refs_and_options(
    tmp_path: Path, command: tuple[str, ...]
) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    result = run(GUARD, *command, cwd=repo, env=inert_remote_git(tmp_path))

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("operation", ["fetch", "pull", "push", "ls-remote"])
def test_canonical_backend_url_is_an_explicit_remote_target(tmp_path: Path, operation: str) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)

    result = run(GUARD, operation, BACKEND, cwd=repo, env=inert_remote_git(tmp_path))

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("target", [BACKEND, FRONTEND])
def test_submodule_add_accepts_only_exact_allowlist_urls(tmp_path: Path, target: str) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)

    result = run(
        GUARD,
        "submodule",
        "add",
        target,
        "vendor/x",
        cwd=repo,
        env=inert_remote_git(tmp_path),
    )

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("target_kind", ["absolute", "relative", "scp"])
def test_submodule_set_url_rejects_non_allowlist_without_mutation(
    tmp_path: Path, target_kind: str
) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    source = tmp_path / "local-source"
    subprocess.run(["git", "init", "-q", "--bare", source], check=True)
    gitmodules = repo / ".gitmodules"
    gitmodules.write_text(f'[submodule "vendor/x"]\n\tpath = vendor/x\n\turl = {BACKEND}\n')
    targets = {
        "absolute": str(source),
        "relative": "../local-source",
        "scp": "other@github.com:Olivermugambi/not-authorized.git",
    }

    result = run(GUARD, "submodule", "set-url", "vendor/x", targets[target_kind], cwd=repo)

    assert result.returncode == 77
    assert f"url = {BACKEND}" in gitmodules.read_text()
    assert targets[target_kind] not in gitmodules.read_text()


@pytest.mark.parametrize("target", [BACKEND, FRONTEND])
def test_submodule_set_url_accepts_exact_allowlist(tmp_path: Path, target: str) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    gitmodules = repo / ".gitmodules"
    gitmodules.write_text(f'[submodule "vendor/x"]\n\tpath = vendor/x\n\turl = {BACKEND}\n')

    result = run(GUARD, "submodule", "set-url", "--", "vendor/x", target, cwd=repo)

    assert result.returncode == 0, result.stderr
    assert f"url = {target}" in gitmodules.read_text()


@pytest.mark.parametrize("operation", ["add", "update"])
def test_submodule_reference_repository_options_fail_closed(tmp_path: Path, operation: str) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    reference = tmp_path / "reference"
    subprocess.run(["git", "init", "-q", "--bare", reference], check=True)
    command = (
        ("submodule", "add", "--reference", str(reference), BACKEND, "vendor/x")
        if operation == "add"
        else ("submodule", "update", "--reference", str(reference), "--init")
    )

    result = run(GUARD, *command, cwd=repo)

    assert result.returncode == 77


def test_clone_reference_repository_option_fails_closed(tmp_path: Path) -> None:
    reference = tmp_path / "reference"
    subprocess.run(["git", "init", "-q", "--bare", reference], check=True)

    result = run(GUARD, "clone", "--reference", str(reference), BACKEND, cwd=tmp_path)

    assert result.returncode == 77


@pytest.mark.parametrize(
    "global_options",
    [
        ("-C", "."),
        ("--git-dir", ".git", "--work-tree", "."),
        ("--git-dir=.git", "--work-tree=."),
        ("-c", "protocol.version=2"),
    ],
)
def test_global_options_cannot_hide_denied_fetch(
    tmp_path: Path, global_options: tuple[str, ...]
) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    env, marker = transport_sentinel(tmp_path)

    result = run(GUARD, *global_options, "fetch", THIRD, cwd=repo, env=env)

    assert result.returncode == 77
    assert not marker.exists()


def test_backend_checkout_rejects_frontend_as_an_added_remote(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)

    result = run(GUARD, "remote", "add", "frontend", FRONTEND, cwd=repo)

    assert result.returncode == 77
    assert run("git", "remote", cwd=repo).stdout.strip() == "origin"


def test_frontend_clone_is_an_allowed_synchronization_surface(tmp_path: Path) -> None:
    result = run(GUARD, "clone", FRONTEND, "frontend", cwd=tmp_path, env=inert_git(tmp_path))

    assert result.returncode == 0, result.stderr


def test_url_rewrite_configuration_cannot_redirect_an_allowed_clone(tmp_path: Path) -> None:
    env, marker = transport_sentinel(tmp_path)

    result = run(
        GUARD,
        "-c",
        f"url.{THIRD}.insteadOf={BACKEND}",
        "clone",
        BACKEND,
        cwd=tmp_path,
        env=env,
    )

    assert result.returncode == 77
    assert not marker.exists()


def test_environment_injected_url_rewrite_is_rejected_before_transport(tmp_path: Path) -> None:
    env, marker = transport_sentinel(tmp_path)
    env.update(
        {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": f"url.{THIRD}.insteadOf",
            "GIT_CONFIG_VALUE_0": BACKEND,
        }
    )

    result = run(GUARD, "clone", BACKEND, cwd=tmp_path, env=env)

    assert result.returncode == 77
    assert not marker.exists()


def test_global_config_url_rewrite_is_rejected_before_transport(tmp_path: Path) -> None:
    env, marker = transport_sentinel(tmp_path)
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    (fake_home / ".gitconfig").write_text(f'[url "{THIRD}"]\n\tinsteadOf = {BACKEND}\n')
    env["HOME"] = str(fake_home)

    result = run(GUARD, "clone", BACKEND, cwd=tmp_path, env=env)

    assert result.returncode == 77
    assert not marker.exists()


def test_included_config_url_rewrite_is_rejected_before_transport(tmp_path: Path) -> None:
    env, marker = transport_sentinel(tmp_path)
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    included = fake_home / "transport.conf"
    included.write_text(f'[url "{THIRD}"]\n\tinsteadOf = {BACKEND}\n')
    (fake_home / ".gitconfig").write_text(f"[include]\n\tpath = {included}\n")
    env["HOME"] = str(fake_home)

    result = run(GUARD, "clone", BACKEND, cwd=tmp_path, env=env)

    assert result.returncode == 77
    assert not marker.exists()


def test_local_config_url_rewrite_is_rejected_before_clone_transport(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    subprocess.run(["git", "-C", repo, "config", f"url.{THIRD}.insteadOf", BACKEND], check=True)
    env, marker = transport_sentinel(tmp_path)

    result = run(GUARD, "clone", BACKEND, cwd=repo, env=env)

    assert result.returncode == 77
    assert not marker.exists()


@pytest.mark.parametrize(
    "variable",
    ["GIT_SSH_COMMAND", "GIT_SSH", "GIT_PROXY_COMMAND", "GIT_EXEC_PATH", "GIT_ASKPASS"],
)
def test_transport_command_environment_override_is_rejected(tmp_path: Path, variable: str) -> None:
    marker = tmp_path / "transport-command-ran"
    env = os.environ.copy()
    env[variable] = f"touch {marker}"

    result = run(
        GUARD,
        "clone",
        "git@github.com:Olivermugambi/ameru-cultural-library-backend.git",
        cwd=tmp_path,
        env=env,
    )

    assert result.returncode == 77
    assert not marker.exists()


def test_cli_exec_path_override_is_rejected_before_transport(tmp_path: Path) -> None:
    env, marker = transport_sentinel(tmp_path)

    result = run(GUARD, "--exec-path", str(tmp_path), "clone", BACKEND, cwd=tmp_path, env=env)

    assert result.returncode == 77
    assert not marker.exists()


def test_recursive_clone_is_rejected_before_uninspected_submodule_transport(tmp_path: Path) -> None:
    env = inert_git(tmp_path)
    marker = tmp_path / "git-invoked"
    git = Path(env["PATH"].split(":", 1)[0]) / "git"
    git.write_text(f"#!/bin/sh\n[ \"$1\" = config ] && exit 1\ntouch '{marker}'\nexit 0\n")

    result = run(GUARD, "clone", "--recurse-submodules", BACKEND, cwd=tmp_path, env=env)

    assert result.returncode == 77
    assert not marker.exists()


def test_backend_checkout_cannot_fetch_frontend_directly(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    env, marker = transport_sentinel(tmp_path)

    result = run(GUARD, "fetch", FRONTEND, cwd=repo, env=env)

    assert result.returncode == 77
    assert not marker.exists()


def test_existing_unauthorized_origin_fails_before_fetch_transport(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo, THIRD)
    env, marker = transport_sentinel(tmp_path)

    result = run(GUARD, "fetch", "origin", cwd=repo, env=env)

    assert result.returncode == 77
    assert not marker.exists()


def test_submodule_update_rejects_unauthorized_gitmodules_url(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    (repo / ".gitmodules").write_text(
        '[submodule "third"]\n\tpath = vendor/third\n\turl = ' + THIRD + "\n"
    )
    env, marker = transport_sentinel(tmp_path)

    result = run(GUARD, "submodule", "update", "--init", cwd=repo, env=env)

    assert result.returncode == 77
    assert not marker.exists()


def test_submodule_update_rejects_unauthorized_local_url_override(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    subprocess.run(["git", "-C", repo, "config", "submodule.frontend.url", THIRD], check=True)
    env, marker = transport_sentinel(tmp_path)

    result = run(GUARD, "submodule", "update", "--init", cwd=repo, env=env)

    assert result.returncode == 77
    assert not marker.exists()


def test_submodule_foreach_is_rejected_as_an_unguarded_command_surface(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)

    result = run(GUARD, "submodule", "foreach", "git fetch", cwd=repo)

    assert result.returncode == 77


def test_install_is_idempotent_and_activates_executable_hook(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    policy = repo / ".project-policy"
    hooks = repo / ".githooks"
    policy.mkdir()
    hooks.mkdir()
    (policy / "git-guard").write_bytes(GUARD.read_bytes())
    (policy / "install.sh").write_bytes(INSTALL.read_bytes())
    (hooks / "pre-push").write_bytes(PRE_PUSH.read_bytes())

    first = run("bash", policy / "install.sh", cwd=repo)
    second = run("bash", policy / "install.sh", cwd=repo)

    assert first.returncode == second.returncode == 0
    assert run("git", "config", "--local", "core.hooksPath", cwd=repo).stdout.strip() == ".githooks"
    assert os.access(policy / "git-guard", os.X_OK)
    assert os.access(hooks / "pre-push", os.X_OK)


@pytest.mark.parametrize(
    "url", [BACKEND, "git@github.com:Olivermugambi/ameru-cultural-library-backend.git"]
)
def test_pre_push_allows_backend_destination(tmp_path: Path, url: str) -> None:
    result = run(PRE_PUSH, "origin", url, cwd=tmp_path)

    assert result.returncode == 0


@pytest.mark.parametrize("url", [FRONTEND, THIRD])
def test_pre_push_rejects_every_non_backend_destination(tmp_path: Path, url: str) -> None:
    result = run(PRE_PUSH, "origin", url, cwd=tmp_path)

    assert result.returncode == 77
