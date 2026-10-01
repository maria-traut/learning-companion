---
name: release-ticket
description: Deliver a reviewed ticket to main via the gitflow - squash-merge the feature PR into develop, sync main into develop with a merge commit, merge the promotion PR develop -> main, then mark the ticket Done in the backlog, the GitHub issue, and the project board. Fifth phase of the development workflow. Use after final-review, when the phase is done.
---

# Release a ticket

Takes a ticket whose review passed (phase `done`, feature PR open against `develop`) all the way to `main`. Every step is idempotent: it checks GitHub's actual state first, so a re-run after an interruption resumes where it stopped.

Config (`.claude/hooks/config.sh`): `INTEGRATION_BRANCH` (develop), `PROTECTED_BRANCHES` (main), `GH_OWNER`/`GH_REPO`. Board/issue updates go through `bash .claude/scripts/board.sh`.

## Preconditions

Read `.claude/state/workflow.json`: phase must be `done`, and `ticket`, `branch`, `issue` (may be empty for tickets without an issue) must be set. `work/<id>/review.md` must say `Verdict: PASS`. If not, stop and say which one failed.

Run every `git push` as its own Bash command (not chained after a commit) — the push gate scans the whole command line.

## Steps

1. **Mark delivered on the feature branch.** On `<branch>`: in `work/backlog.md`, change this ticket's line from `- [~] <id>: ...` to `- [x] <id>: ... — see work/<id>/review.md`. Then:

   ```bash
   git add work/backlog.md && git commit -m "docs(<id>): mark ticket delivered"
   ```
   ```bash
   git push
   ```

   Skip if the line is already `[x]`. This way the backlog flips to done in the same release that puts the feature on main.

2. **Squash-merge the feature PR into develop.** Find it with `gh pr list --head <branch> --base develop --state all --json number,state`. If it is `OPEN`:

   ```bash
   gh pr merge <pr> --squash --delete-branch --subject "<PR title> (#<pr>)"
   ```

   The PR title is already the Conventional Commit line (`feat(<id>): ...` / `fix(<id>): ...`). If the merge is refused (conflicts with develop), stop and report — do not resolve feature conflicts here; that is a new plan step for `tdd-implement`.

3. **Sync main into develop.**

   ```bash
   git fetch origin && git switch develop && git pull --ff-only
   git merge-base --is-ancestor origin/main develop && echo in-sync
   ```

   If not in sync: `git merge --no-ff origin/main -m "chore(release): merge main into develop"`. On conflicts, resolve them so develop's intent wins unless main carries a fix develop lacks, then run the suite and lint and conclude with `git commit -m "chore(release): merge main into develop"` (the commit gate requires green). Never resolve by discarding a side wholesale without reading it. If the suite stays red, `git merge --abort` and stop with a report. Then:

   ```bash
   git push origin develop
   ```

4. **Promote develop to main.** Reuse an open PR from `develop` to `main` if one exists, otherwise:

   ```bash
   gh pr create --base main --head develop --title "chore(release): promote <id> to main" --body-file - <<'EOF'
   Promotes <PR title> (#<pr>).

   Closes #<issue>

   Review: work/<id>/review.md
   EOF
   ```

   Wait for its required checks (`gh pr checks <pr> --watch --fail-fast`). If a check fails, stop and report. Then merge with a merge commit (main and develop keep a shared history):

   ```bash
   gh pr merge <release-pr> --merge --subject "chore(release): promote <id> to main (#<release-pr>)"
   ```

5. **Mark Done on GitHub** (only once step 4 is merged):

   ```bash
   bash .claude/scripts/board.sh status <issue> Done
   bash .claude/scripts/board.sh close <issue> "Released to main in #<release-pr>."
   ```

   The issue may already be closed by the release PR's `Closes #<issue>`; `close` is then a no-op worth ignoring.

6. **Finish.**

   ```bash
   git switch develop && git pull --ff-only
   bash .claude/hooks/set-state.sh phase released
   ```

   Report: feature PR, release PR, issue, and that the ticket is on main.

## Hard limits

- Never push to `main`, never merge locally into `main`, never force-push `develop` (all enforced by hooks).
- Never merge a PR whose checks are failing, and never bypass branch protection.
- Never mark the issue/board Done before the promotion PR is merged.
