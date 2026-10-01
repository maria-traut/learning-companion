---
name: refine-ticket
description: Turn a rough ticket or feature idea into a refined ticket with acceptance criteria. First phase of the development workflow; starts a new ticket, creates the feature/fix branch from develop, and moves the ticket to In Progress in the backlog and on the GitHub project board. Use when the user brings a new task, story, or bug report.
---

# Refine a ticket

Input: the user's rough ticket — pasted text, a file path, a one-line idea, or a `work/backlog.md` line (`$ARGUMENTS` if provided). A backlog line carries its GitHub issue as `#<n>` (e.g. `#1 Base layout and home page: ...`); a GitHub issue number or URL given directly works the same way (`gh issue view <n>` for its text).

## Preconditions

Read `.claude/state/workflow.json` (if it exists). If a ticket is already in progress (phase is not `idle` or `released`), stop and ask the user whether to abandon it or finish it first. Do not silently start a second ticket. A ticket in phase `done` is not finished yet — it still needs `release-ticket`.

## Steps

1. Derive a short kebab-case ticket id from the task (e.g. `comments-endpoint`) and its kind: `feature` for new behaviour, `fix` for a bug report. Confirm them with the user if the task is ambiguous. If the task has no GitHub issue yet, create one (`gh issue create --repo <GH_OWNER>/<GH_REPO> --title ... --body ...`), add it to the board (`board.sh status <n> Todo`), and append it to `work/backlog.md` as `- [ ] #<n> <description>`.
2. Investigate context cheaply: use one `Explore` sub-agent to find the parts of the codebase the ticket touches. Do not read whole modules into the main context — you only need enough to ask informed questions.
3. Interview the user. Ask about anything that changes scope or design, typically: expected behaviour and edge cases, validation and error responses, auth requirements, out-of-scope items. Ask in one batch, not one question per turn.
4. Write `work/<id>/ticket.md`:

   ```markdown
   # <Title>                     <!-- one line -->
   ## Story
   As a ..., I want ..., so that ...
   ## Acceptance criteria
   - [ ] AC1 ... (concrete, testable, one behaviour each)
   ## Out of scope
   ## Notes
   Open questions that were answered, relevant constraints.
   ```

   Every acceptance criterion must be verifiable by a test. If you cannot phrase it as a test, refine it further.
   Put `Issue: #<n>` as the first line under `## Notes`.
5. Create the branch from an up-to-date develop and record the state (`<kind>` is `feature` or `fix`):

   ```bash
   git fetch origin && git switch develop && git pull --ff-only
   git switch -c <kind>/<id>
   bash .claude/hooks/set-state.sh phase refined ticket <id> branch <kind>/<id> issue <n>
   ```

   Uncommitted backlog edits (e.g. a `[[parked: ...]]` tag) come along onto the new branch; that is intended.
6. **Sync status to In Progress** — backlog and board together. In `work/backlog.md`, rewrite the ticket's line from `- [ ] #<n> <description>` to `- [~] <id>: #<n> <description>` (drop any `[[parked: ...]]` tag). Then:

   ```bash
   bash .claude/scripts/board.sh status <n> "In Progress"
   git add work/<id>/ticket.md work/backlog.md && git commit -m "docs(<id>): refined ticket"
   ```

7. Show the user the acceptance criteria and ask for approval. On approval, tell them the next step is `plan-ticket`. Do not start planning in the same breath unless the user asks you to continue.

## Hard limits

- Do not touch any source code in this phase.
- Do not propose an implementation; that is the plan phase's job.
