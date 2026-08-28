# Contributing

Read `ARCHITECTURE.md`, `DOMAIN_MODEL.md`, `CONTENT_GOVERNANCE.md`, and `MEDIA_POLICY.md` before changing domain or API behavior.

Every feature should include tests and preserve the full verification gate. Prefer extending an existing domain model or service over adding parallel concepts. API changes must update the relevant contract documentation.

Never invent cultural, historical, provenance, attribution, or licensing facts to make fixtures look realistic. Clearly label synthetic fixtures.

Do not couple frontend presentation concerns to backend domain models. Do not add authentication, CMS, moderation, or persistence infrastructure unless the corresponding product scope has been approved.

All implementation work must follow the dedicated issue branch, worktree,
rebase, validation, merge, and cleanup lifecycle in `GIT_WORKFLOW.md`.

## Issue and pull request contracts

Start implementation work from the repository's structured implementation issue
form. Use the epic form when decomposing a milestone: child scopes must be
disjoint and every shared interface must name the exact artifact or contract one
child publishes and another consumes. Do not use an epic as a shared
implementation branch. Write mandatory acceptance criteria as Markdown
checkboxes so their disposition remains explicit through review.

Pull requests must use the repository template and reproduce every mandatory
acceptance criterion from the linked issue. An unchecked mandatory acceptance
criterion blocks merge. A checkbox is a disposition, not evidence: every checked
criterion must link to an automated validation result or recorded manual proof.

Record automated and manual evidence separately. If remaining manual verification
does not block the issue's expected state, open and link a follow-up issue before
merge. Never hide an incomplete manual check in prose or treat it as complete. If
the missing evidence is mandatory for the issue, leave its criterion unchecked
and stop.

When work discovers an out-of-scope blocker, open and link a separate issue rather
than absorbing the change. Stop implementation when that blocker is a
prerequisite to satisfying the current issue. Otherwise preserve it as an
explicitly non-blocking follow-up without widening the reviewed diff.

The issue and pull request templates consume the branch, worktree, rebase,
validation, merge, and cleanup rules in `GIT_WORKFLOW.md`; they do not redefine
those Git mechanics. Final evidence is valid only for the PR head produced after
the last rebase and complete validation rerun.
