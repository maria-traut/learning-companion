#!/usr/bin/env bash
# PreToolUse hook for Bash.
# Gitflow gates: no commits on protected branches, commits on develop only to
# conclude a main->develop sync merge, no commits with red tests, no
# --no-verify, no direct push to protected branches, no push or PR merge
# before the review has passed, no force-push to shared branches.
# Exit 2 blocks the command; stderr is fed back to Claude.
source "$(dirname "$0")/lib.sh"

input="$(cat)"
cmd="$(jq -r '.tool_input.command // empty' <<<"$input")"
[ -z "$cmd" ] && exit 0

# Matches `git <sub>` including global options in between (git -c k=v -C dir <sub>).
is_git() {
  echo "$cmd" | grep -qE "(^|[;&|(]\s*)git(\s+-[cC]\s+\S+|\s+--?[a-z-]+(=\S+)?)*\s+$1\b"
}

is_gh_pr_merge() {
  echo "$cmd" | grep -qE "(^|[;&|(]\s*)gh\s+pr\s+merge\b"
}

suite_is_green() {
  [ ! -f "$PROJECT_MARKER" ] || $TEST_CMD >/dev/null 2>&1
}

phase="$(current_phase)"
branch="$(current_branch)"
shared_branches="$PROTECTED_BRANCHES|$INTEGRATION_BRANCH"

if is_git "commit"; then
  if echo "$cmd" | grep -qE -- "--no-verify|\s-n\b"; then
    echo "BLOCKED by workflow: 'git commit --no-verify' is not allowed. Commit hooks are part of the quality gate." >&2
    exit 2
  fi
  if echo "$branch" | grep -qE "^($PROTECTED_BRANCHES)$"; then
    echo "BLOCKED by workflow: direct commits to '$branch' are not allowed. '$branch' only changes via a promotion PR from '$INTEGRATION_BRANCH' (release-ticket skill)." >&2
    exit 2
  fi
  if [ "$branch" = "$INTEGRATION_BRANCH" ]; then
    if ! git rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1; then
      echo "BLOCKED by workflow: direct commits to '$INTEGRATION_BRANCH' are not allowed. Work happens on feature/<id> or fix/<id> (refine-ticket creates it) and lands via a squash-merged PR. The only commit allowed here concludes a main->$INTEGRATION_BRANCH sync merge (release-ticket skill)." >&2
      exit 2
    fi
    if ! suite_is_green; then
      echo "BLOCKED by workflow: the suite is red after the main->$INTEGRATION_BRANCH sync merge. Fix the conflict resolution before committing ($TEST_CMD)." >&2
      exit 2
    fi
  fi
  if [ "$phase" = "idle" ]; then
    echo "BLOCKED by workflow: no ticket is in progress (phase: idle). Start with the refine-ticket skill before committing." >&2
    exit 2
  fi
  if [ "$phase" = "implementing" ] || [ "$phase" = "reviewing" ]; then
    if ! suite_is_green; then
      echo "BLOCKED by workflow: the test suite is red. Commits are only allowed on green. Finish the current TDD cycle first ($TEST_CMD)." >&2
      exit 2
    fi
  fi
fi

if is_git "merge" && echo "$branch" | grep -qE "^($PROTECTED_BRANCHES)$"; then
  echo "BLOCKED by workflow: merging locally into '$branch' is not allowed. '$branch' only changes via a promotion PR from '$INTEGRATION_BRANCH'." >&2
  exit 2
fi

if is_git "push"; then
  if echo "$cmd" | grep -qE -- "--force|--force-with-lease|\s-f\b|\s\+\S" && echo "$cmd $branch" | grep -qwE "($shared_branches)"; then
    echo "BLOCKED by workflow: force-pushing to a shared branch ($shared_branches) is not allowed." >&2
    exit 2
  fi
  if echo "$cmd" | grep -qE -- "--all|--mirror"; then
    echo "BLOCKED by workflow: 'git push --all/--mirror' would push protected branches. Push the one branch you mean." >&2
    exit 2
  fi
  if echo "$cmd" | grep -qwE "($PROTECTED_BRANCHES)" \
     || { echo "$branch" | grep -qE "^($PROTECTED_BRANCHES)$" && ! echo "$cmd" | grep -qE "push\s+\S+\s+\S+"; }; then
    echo "BLOCKED by workflow: direct pushes to a protected branch are not allowed. Open a promotion PR from '$INTEGRATION_BRANCH' instead (release-ticket skill)." >&2
    exit 2
  fi
  if [ "$phase" != "done" ]; then
    echo "BLOCKED by workflow: pushing requires a passed final review (current phase: $phase). Run the final-review skill; it sets the phase to 'done' on a PASS verdict." >&2
    exit 2
  fi
fi

if is_gh_pr_merge && [ "$phase" != "done" ]; then
  echo "BLOCKED by workflow: merging PRs requires a passed final review (current phase: $phase). Merges happen in the release-ticket skill, in phase 'done'." >&2
  exit 2
fi

exit 0
