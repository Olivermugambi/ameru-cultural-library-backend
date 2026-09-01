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

## Required CI

Pull requests and pushes to `main` run the stable `P0 required checks` job in
the `CI` workflow. That check is blocking and performs dependency installation,
package build/import validation, Ruff, shell syntax validation, the explicit
repository-boundary suite, and the complete unfiltered pytest suite. The
repository-boundary tests therefore run both as a visible P0 policy gate and as
part of the full regression suite.

The workflow has read-only repository permission and cancels only superseded
runs for the same pull request or Git ref. Main-branch enforcement must require
the exact `P0 required checks` context observed on a successful pull request;
do not guess or rename the context after enabling the rule.

For Docker-based clean-checkout reproduction and manual verification, use
[`docs/local-reproduction.md`](docs/local-reproduction.md). That guide owns the
Compose lifecycle, test-container command, expected endpoint results, logs, and
project-scoped teardown procedure.

## Repository-boundary validation

Bootstrap the boundary in every fresh backend checkout, then run its stable
validation command:

```bash
bash .project-policy/install.sh
python -m pytest tests/test_repository_boundary.py
```

The backend checkout must have exactly one remote, `origin`, whose fetch and
push URLs both normalize to the backend repository. Frontend synchronization
is allowed by cloning its canonical HTTPS or SSH URL into a separate checkout,
or through the approved connector; it is not allowed by adding the frontend as
a backend remote.

The guard is a narrow gateway for the explicitly supported remote operations
`clone`, `fetch`, `pull`, `push`, `ls-remote`, and safe read-only
`remote` queries. Every other command fails closed with policy exit code
`77`, including commands added by a future Git version. Use ordinary `git`
directly for local-only work; do not route local commands through the remote
gateway.

The test matrix covers canonical HTTPS and SSH URLs with optional `.git` and
trailing slash, Git global options, supported remote commands, unsupported
command fallthrough, remote mutation, bootstrap, and the backend-only pre-push
hook. Denial cases use inert fixtures and Git/transport sentinels, so no
unauthorized repository is contacted.

For fetch, pull, push, and ls-remote, repository operands are parsed separately
from later refs and refspecs. Only `origin` or a canonical backend URL is a
valid backend-checkout target; filesystem paths, other remote names, and other
scp-like hosts fail closed. Clone accepts either allowlisted repository into a
separate checkout. All guarded `submodule` commands are prohibited: neither
the frontend, backend, nor any third repository may become a backend submodule
or other repository-graph dependency. Reference-repository, recursive-clone,
and recursive `fetch`, `pull`, and `push` options also fail closed because they
introduce an additional repository access surface.

Before a guarded remote operation, the guard inspects effective Git config
(including included files) and rejects URL rewrites, config includes, custom
SSH commands, and the external transport protocol. Equivalent command-line and
environment overrides—including `GIT_CONFIG_COUNT`, `GIT_SSH_COMMAND`, and
`GIT_EXEC_PATH`—also fail closed. Remove the override rather than bypassing the
guard. Ordinary credential helpers and HTTPS proxy routing remain Git/host
configuration responsibilities; this policy validates repository identity but
is not a network or credential sandbox.

These scripts enforce only guarded shell invocations and pushes through the
configured hook. Agent instructions govern direct Git binary and connector
use; the scripts do not claim to sandbox or intercept those independent paths.

## Implementation order
1. Approve domain and API contracts.
2. Add deterministic fixtures only where needed for UI integration.
3. Implement repository interfaces and service logic.
4. Expose validated API routes.
5. Add contract/domain/API tests.
6. Only then introduce persistence or external integrations.

## Stop conditions
Stop rather than inventing data when a required cultural fact is unknown. Stop before changing a public API shape if the frontend contract has already been consumed. Stop before adding infrastructure that is not required by an accepted feature.
