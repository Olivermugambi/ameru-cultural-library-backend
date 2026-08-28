# Issue Worktree Lifecycle

Every implementation issue uses exactly one dedicated branch and one dedicated
worktree. Never implement on `main`, share a branch between issues, or put a
worktree inside either repository checkout.

## Stable interface for issue and PR templates

- Branch: `<milestone>/<issue-number>-<short-slug>` (for example,
  `p0/65-worktree-branch-lifecycle`).
- Worktree: a sibling collection named `<repository>-worktrees/issue-<number>`.
- Creation: `.project-policy/worktree-lifecycle create ISSUE SLUG MILESTONE`.
- Cleanup: `.project-policy/worktree-lifecycle cleanup ISSUE`.
- One issue number must map to exactly one local issue branch and worktree.
- Final validation must run after the last rebase.
- The normal GitHub merge method is **Rebase and merge**, never merge-commit or
  squash merge.

The backend and frontend are separate checkouts. Do not add the frontend as a
worktree or nest either checkout in the other. The repository boundary and its
guarded remote commands remain defined by `AGENTS.md`; this lifecycle does not
modify that allowlist.

## Start an issue

1. From the clean backend `main` checkout, install the repository policy and
   synchronize the canonical base:

   ```bash
   bash .project-policy/install.sh
   .project-policy/git-guard fetch origin main
   git switch main
   git merge --ff-only origin/main
   ```

2. Confirm the issue has no existing branch or worktree, then create it:

   ```bash
   .project-policy/worktree-lifecycle create 65 worktree-branch-lifecycle p0
   ```

The helper fails closed when the base is dirty, is not `main`, differs from the
locally fetched `origin/main`, the issue already maps to a branch, the target
exists, or the requested root is nested in the checkout. It never fetches,
resets, removes, or overwrites work.

## Synchronize and open a PR

Remote synchronization always uses the guarded command described in
`AGENTS.md`. In the issue worktree:

```bash
.project-policy/git-guard fetch origin main
git status --short
git rebase origin/main
```

If a conflict occurs, inspect each conflict and resolve only issue-scoped
changes. Stage the resolved files and use `git rebase --continue`. If safe
resolution would exceed the issue scope, use `git rebase --abort`, open the
required blocker issue, and stop. Never use a destructive reset to escape a
conflict.

Run the repository's full validation gate after this rebase, inspect
`git diff origin/main...HEAD`, and push the issue branch through the repository
guard. Record the branch, worktree convention, rebase base SHA, validation
commands, and scoped diff in the PR.

## Final validation and merge

Immediately before merge:

1. Guard-fetch `origin/main` again.
2. Rebase the issue branch onto that exact `origin/main`.
3. Rerun every required test, lint, policy, and issue-specific validation.
4. Push the rebased branch and wait for required CI on the new head SHA.
5. Verify all acceptance criteria and adversarial-review findings are resolved.
6. Select GitHub **Rebase and merge**.

Do not select **Create a merge commit** or **Squash and merge**. Evidence should
include the final branch head SHA, base SHA, passing CI run, selected merge
method, and the resulting linear `main` history. A rebase changes commit
identity, so evidence from a pre-rebase head is stale.

## Cleanup

After GitHub reports the PR merged, update the base checkout's remote-tracking
state, then run cleanup from outside the issue worktree:

```bash
cd /path/to/ameru-cultural-library-backend
.project-policy/git-guard fetch origin main
.project-policy/worktree-lifecycle cleanup 65
```

Cleanup requires a clean worktree and uses `git cherry` to prove that every
branch patch is represented in `origin/main`. This accommodates GitHub's
rebase-created commit identities while refusing uncommitted or unintegrated
work. It uses ordinary `git worktree remove`, then deletes only the branch ref
whose exact reviewed SHA was proven patch-equivalent. It never force-removes a
worktree or changes a branch that moved during cleanup. Branch deletion is a
compare-and-swap operation: if the ref changes after proof, Git refuses the
deletion and retains the moved branch for inspection.

## Recovery without data loss

- **Interrupted implementation:** return to the issue worktree, inspect
  `git status`, and continue or commit the issue-scoped work. Do not create a
  replacement branch for the same issue.
- **Interrupted rebase:** inspect `git status`; continue after deliberate
  conflict resolution, or use `git rebase --abort` to restore the pre-rebase
  branch. Never delete the worktree while rebase state exists.
- **Stale metadata:** first run `git worktree list --porcelain` and verify the
  recorded path is genuinely absent. Use `git worktree prune --dry-run` before
  `git worktree prune`. Do not prune merely because a path is inconvenient or
  temporarily unavailable.
- **Abandoned work:** preserve the worktree and branch, record why work stopped
  on the issue, and hand it over explicitly. Cleanup is allowed only after its
  commits are integrated or a reviewer deliberately resolves their disposition
  outside this helper.
- **Existing target or ambiguous issue branch:** inspect both with
  `git worktree list` and `git branch --list`. Reuse only when they are the same
  issue's intentionally preserved work; otherwise stop and resolve the naming
  conflict without deleting either.

These recovery steps favor preservation. The helper intentionally provides no
force-delete, force-reset, automatic conflict resolution, or abandoned-branch
deletion mode.
