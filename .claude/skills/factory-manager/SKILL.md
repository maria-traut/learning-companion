---
name: factory-manager
description: Inspects the ticket backlog and the current workflow phase, then triggers the one pipeline skill (refine-ticket, plan-ticket, tdd-implement, final-review, or release-ticket) that owns the next step. Picks the next queued ticket once the previous one has landed on main (phase released) or nothing is in progress (idle). Advances the pipeline by exactly one step per call and reports cleanly, so it is safe to invoke repeatedly, including from a loop. Use when the user wants the AI factory to keep moving without manually tracking phase and ticket state themselves.
---

# Manage the AI factory

Orchestrates the pipeline defined in `.claude/rules/workflow.md`. This skill never changes `phase` itself, never writes source code, and never invokes more than one phase skill per call — it only reads state, decides which phase skill owns the next step, and triggers it with the `Skill` tool. All actual work and every phase transition still happens inside `refine-ticket`, `plan-ticket`, `tdd-implement`, `final-review`, and `release-ticket`.

Status sync is owned by the transition skills, so backlog, GitHub issue and project board always move together: `refine-ticket` sets `[~]` + board "In Progress", `release-ticket` sets `[x]` + board "Done" + closes the issue once the ticket is on `main`. Backlog lines reference their issue as `#<n>`.

## Preconditions

1. Read `.claude/state/workflow.json`. It may not exist yet — treat a missing file or a missing `phase` key as phase `idle`, exactly like `lib.sh:current_phase` does. Note `ticket` the same way (missing = none).
2. Read `work/backlog.md`. If it doesn't exist, create it with just this header, then stop this call and report that the backlog is empty and needs entries:

   ```markdown
   # Ticket backlog

   Queue for `factory-manager`. One idea per line, top to bottom = priority order.
   The pipeline skills own the status marker, the ticket id, and the `[[parked: ...]]`
   annotation on each line — add new ideas as plain `- [ ] #<issue> <description>` lines
   (or plain `- [ ] <description>`; refine-ticket then creates the issue) and leave the
   rest alone.
   ```

## Steps

Do exactly one of the following, then stop and report (step 5). Never chain two phase skills in one call — one call is one observable pipeline step.

1. **Idempotence check.** If `ticket` is set, find its line in `work/backlog.md`. If that line carries `[[parked: <skill> @ <phase>]]` and `<phase>` equals the *current* phase, the last call already triggered `<skill>` at this phase and it stopped to ask a human something, and nothing has moved since. Do not re-invoke it — go straight to step 5 and report that it is still waiting. Otherwise (no tag, or the tag's phase no longer matches — meaning progress happened since) continue normally and discard any stale tag when you next touch that line.

2. **Dispatch on phase:**

   | phase | action |
   |---|---|
   | `idle` or `released` | Close-out + selection, below. |
   | `refined` | Invoke `plan-ticket`. |
   | `planned` | Invoke `tdd-implement`. |
   | `implementing` | Invoke `tdd-implement` (it resumes from the plan itself). |
   | `reviewing` | Invoke `final-review`. |
   | `done` | Invoke `release-ticket` (squash-merge into develop, promote to main, mark Done). |

3. **`idle`/`released` — close-out.** Confirm the previous ticket really landed: when `phase` is `released`, its backlog line must be `[x]` and `gh issue view <issue> --json state` must say `CLOSED`; if not, stop and report the mismatch instead of picking a new ticket. Then run `git status`; if the tree isn't clean apart from backlog edits, stop and report it. Then `git fetch origin && git switch develop && git pull --ff-only` — every ticket branches off an up-to-date `develop`, never off `main` or the finished branch.

4. **`idle`/`released` — selection.** Read the backlog top to bottom and pick the first `[ ]` line, skipping any whose description names a dependency that's still open (e.g. "after X ships") — log a skip like that rather than guessing an order, and ask the user only if two candidates are genuinely ambiguous in priority. If no eligible `[ ]` line exists, report **"Backlog is empty — nothing to do"** and stop; that's the signal for a wrapping loop to stop too.

   Invoke `refine-ticket` with the picked line's text (including its `#<issue>`) as its argument. Afterwards, re-read `.claude/state/workflow.json`:
   - If `phase` is now `refined`, `refine-ticket` has already rewritten the line to `[~] <id>: ...` and moved the board card to In Progress — nothing more to do.
   - If `phase` is still `idle`/`released`, `refine-ticket` stopped mid-interview (or asked for ticket-id confirmation) — leave the line as `- [ ]` but add `[[parked: refine-ticket @ <phase>]]` so the next call doesn't restart the interview from scratch.

5. **Report.** One short summary: phase before → phase after, the ticket id, and the artifact that changed (or the backlog line, for a close-out/selection). If the invoked skill stopped to ask the user something — ticket interview, ticket-id confirmation, plan approval — say exactly that instead of answering on its behalf; a human needs to be present for that turn, and this skill does not fabricate approval to keep a loop moving.

## Hard limits

- Never call `.claude/hooks/set-state.sh`; only the phase skill that owns a transition may change `phase` or `ticket`.
- Never invoke more than one phase skill per call.
- Never fabricate or infer the user's approval of a ticket or plan.
- Never write source code from this skill (the write-protection hook would block it outside `implementing` anyway); it only ever delegates.
- Never reorder or delete backlog lines; this skill only adds or removes a line's `[[parked: ...]]` tag.
- Never merge PRs or touch `main`/`develop` beyond `git switch develop && git pull --ff-only` — merging is `release-ticket`'s job.
- Don't try to commit backlog edits made while `phase` is `idle`/`released` — they would land on `develop`, which only takes PRs. Leave the edit uncommitted; `refine-ticket` carries it onto the new branch and commits it.
