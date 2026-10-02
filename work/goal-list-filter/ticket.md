# Filter the goal list by status via a query parameter

## Story
As a logged-in learner, I want to filter my goal list by status, so that I can focus on the goals that are planned, in progress, or done.

## Acceptance criteria
- [x] AC1 `GET /goals/?status=<value>` with a valid status (`planned`, `in_progress`, `done`) lists only the logged-in user's goals with that status. Goals with other statuses are not shown.
- [x] AC2 Filtering never shows another user's goals, even when they have the requested status.
- [x] AC3 With no `status` parameter, an empty one, or an unknown value (e.g. `?status=foo`), the page returns 200 and lists all of the user's goals, as it does today.
- [x] AC4 A filtered list keeps the existing newest-first order.
- [x] AC5 The goal list page shows a row of filter links: "All" (`/goals/`), then "Planned", "In progress" and "Done" (`/goals/?status=planned`, `?status=in_progress`, `?status=done`).
- [x] AC6 The link for the active filter has `aria-current="page"`, and no other filter link has it. "All" is the active link when no valid status is applied.
- [x] AC7 When a valid filter matches none of the user's goals, the page shows "No goals with status <label>." (e.g. "No goals with status Done."). The "No goals yet." message stays for when no filter is applied and the user has no goals.
- [x] AC8 Anonymous visitors to `/goals/?status=done` are still redirected to login, as they are for `/goals/`.

## Out of scope
- Filtering by anything other than status, such as search, date or tags.
- Filtering on several statuses at once.
- Keeping the active filter after create, edit or delete redirects.
- Pagination.
- JavaScript or a dropdown/form filter UI.

## Notes
Issue: #8

- Interview answers:
  - An invalid or empty value is ignored and all goals are shown, with no 400.
  - The filter UI is plain links, one per status, with `aria-current` on the active one.
  - When a filter matches nothing, the empty message names the filter.
- Status values and labels come from `Goal.Status` (`src/apps/goals/models.py:7-10`). Labels are "Planned", "In progress" and "Done".
- The list view is `GoalListView` (`src/apps/goals/views.py:14`), URL `goals:list` → `/goals/`. It is already scoped to `request.user` via `OwnGoalMixin`.
- Template: `src/apps/goals/templates/goals/goal_list.html`. Tests: `src/apps/goals/tests/test_views.py`. The `create_goal(user, title, status, day)` helper is already there.
