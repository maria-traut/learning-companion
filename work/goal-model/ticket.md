# Goal model owned by a user, with migration and admin

## Story
As a learner, I want my learning goals stored with a title, a description and a status (planned, in progress, done), so that later features (goal pages, sessions, resources, AI summaries, the dashboard) have a goal to hang off. As an admin, I want to manage goals in the Django admin.

## Acceptance criteria
- [x] AC1 A new `goals` app is installed. A `Goal` has `title`, `description`, `status`, `created_at`, `updated_at` and an owning `user`, and is reachable from the user as `user.goals`.
- [x] AC2 `status` only allows `planned`, `in_progress` and `done`, labelled "Planned", "In progress" and "Done". A new goal defaults to `planned`. `full_clean()` rejects any other value.
- [x] AC3 `title` and `description` are both required. `full_clean()` raises a `ValidationError` on `title` when it is empty or longer than 200 characters, and on `description` when it is empty.
- [x] AC4 `created_at` and `updated_at` are set automatically when a goal is created. Saving the goal again leaves `created_at` unchanged and moves `updated_at` forward.
- [x] AC5 A user can own several goals. `user.goals` contains only that user's goals. Deleting a user deletes their goals and leaves other users' goals in place.
- [x] AC6 Goals are ordered newest first by `created_at` by default.
- [x] AC7 `str(goal)` is its title.
- [x] AC8 `Goal` is registered in the admin:
  - Its list and add pages load for a superuser.
  - The list shows title, owner, status, created and updated.
  - It can be filtered by status (`?status=done` shows only done goals) and searched by title (`?q=`).
- [x] AC9 In the admin, a superuser can create a goal for a chosen owner on the add page. On the change page:
  - The owner is read-only, so a POST with a different `user` doesn't reassign the goal.
  - `title`, `description` and `status` stay editable.
  - `created_at` and `updated_at` are shown read-only, not as inputs.

## Out of scope
- User-facing goal views: list/create (#6), detail/edit/delete (#7), status filter (#8).
- Target dates, priorities, tags or rules for which status may follow which.
- Seeding example goals.

## Notes
Issue: #5

- Interview answers (2026-10-02):
  - `status` choices are `planned` / `in_progress` / `done`, labelled "Planned" / "In progress" / "Done", with default `planned`. Underscore values are the usual Django style and are safe in #8's `?status=` filter.
  - `title` (up to 200 characters) and `description` are both required.
  - Default ordering is newest first.
  - Admin follows the Profile pattern: owner selectable on add and read-only on change, plus a status filter, title search and read-only timestamps.
- "Required" is enforced through model and form validation (`full_clean()`, the admin form). The database itself does not reject an empty string for a text column, so tests go through `full_clean()` or the admin.
- Deleting a user cascades to their goals, the same as `Profile` in #3.
- Challenge (`instructions/challenge.md`, line 55): "Create a `Goal` entity: `title`, `description`, `status` (planned / in-progress / done), `created_at`, `updated_at`." The later tickets need these fields: #8 filters by `status` and #17 counts goals per status.
- Current state:
  - Only the `accounts` and `pages` apps exist. CLAUDE.md's "New app" command creates `src/apps/goals/`.
  - `USE_TZ = True`, so timestamps are timezone-aware.
  - Accounts patterns to mirror: `settings.AUTH_USER_MODEL` with an explicit `related_name`, `@admin.register`, and `get_readonly_fields` making the owner read-only on change.
