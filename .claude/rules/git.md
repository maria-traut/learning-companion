# Git conventions (gitflow)

```
feature/<id> ─┐ squash PR                       merge-commit PR
fix/<id> ─────┴──────────► develop ─────────────────────────► main
                              ▲   chore(release): merge main   │
                              └──────── into develop ◄─────────┘ (before each promotion)
```

- **`main`** is protected. It only changes via a promotion PR from `develop`, merged with a merge commit by `release-ticket`. No direct commits, merges or pushes (enforced by hooks and a GitHub ruleset; a CI check rejects PRs into `main` from any other branch).
- **`develop`** is the integration branch. It only changes via squash-merged PRs from `feature/<id>` / `fix/<id>`, plus the sync merge below. No direct commits otherwise (enforced by a hook and a GitHub ruleset).
- **Work branches** are `feature/<id>` (new behaviour) or `fix/<id>` (bug), created from an up-to-date `develop` by `refine-ticket`. Never branch from `main`.
- **Before every promotion** `release-ticket` merges `origin/main` into `develop` with `chore(release): merge main into develop`, resolves any conflicts there, and only pushes on a green suite.
- Every ticket is promoted to `main` before the next ticket starts.

## Commit messages

Conventional Commits, see `.conventionalcommit.json`:

- `feat(<id>): <what the step delivers>` for plan steps on `feature/`, `fix(<id>): ...` on `fix/`.
- `docs(<id>): ...` for workflow artifacts, `refactor(<id>): ...` for pure refactoring, `test(<id>): ...` for test-only corrections.
- `chore(release): ...` for the main→develop sync merge and the promotion PR.
- `chore(repo): ...`, `build(repo): ...`, `ci(repo): ...` for tooling outside a ticket.

The feature PR title is the squash commit on `develop`, so it is `<type>(<id>): <title>`.

## Rules

- Commit after every green TDD cycle. Small commits are the audit trail of the workflow; do not batch several steps into one commit. They are squashed only when the PR lands on `develop`.
- Commits require a green test suite and `--no-verify` is forbidden (both enforced by a hook).
- Pushing and merging PRs are only possible once the final review has passed (phase `done`, enforced by a hook). Run each `git push` as its own command.
- PR bodies reference the issue (`Refs #<n>` on the feature PR, `Closes #<n>` on the promotion PR) and link `work/<id>/review.md`.
- Never force-push or rewrite history on `main` or `develop`.
