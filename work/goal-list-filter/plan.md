# Plan: goal-list-filter

## Research summary
- **View:** `GoalListView(OwnGoalMixin, ListView)` at `src/apps/goals/views.py:14` is a bare `pass`.
  - `OwnGoalMixin.get_queryset` (`views.py:9-11`) returns `self.request.user.goals.all()`. `Meta.ordering = ["-created_at"]` gives newest first.
  - No view reads `request.GET` or overrides `get_context_data` yet.
  - House style: rely on Django defaults (the context name is `goal_list`), call `super()` with no arguments, and keep views minimal.
- **Model:** `Goal.Status` TextChoices (`src/apps/goals/models.py:7-10`): `planned`/"Planned", `in_progress`/"In progress", `done`/"Done".
- **URL:** `goals:list` → `/goals/`, protected by `LoginRequiredMixin`.
- **Template:** `src/apps/goals/templates/goals/goal_list.html`:
  - `<h1>Goals</h1>`, then the "New goal" link `<p>`, then a `<ul>` of goals with `{% empty %}<li>No goals yet.</li>`.
  - No `aria-current` or active-link pattern exists anywhere yet.
  - Pico.css styles `<nav><ul><li><a>` rows. Context processors include `request`. There are no custom template tags.
- **Tests:** `src/apps/goals/tests/test_views.py` (45 passing).
  - Plain pytest-django functions. `@pytest.mark.django_db` goes first, then `@pytest.mark.parametrize(..., ids=[...])`.
  - Helpers: `user` fixture ("ada"), `create_goal(user, title, status, day)` (pins `created_at`), and `main_html(response)` (extracts `<main>`).
  - Second users are created as "grace".
  - Assertion idioms:
    - Links are matched as `<a href="EXACT"[^>]*>\s*Text\s*</a>`.
    - Order is checked with `main.index(a) < main.index(b)`.
    - Matching inside one `<li>` uses the tempered `(?:(?!</li>).)*` pattern.
  - Run with `.venv/bin/pytest src/apps/goals/tests/test_views.py`. `-q` is already in addopts.

## Design decisions
- **Filtering in the view:** `GoalListView` gets a `status_filter` helper that returns the matching `Goal.Status` member, or `None` for a missing, empty or unknown value. `get_queryset` filters `super().get_queryset()` with it.
  - Unknown values are ignored rather than rejected, as agreed in the interview (AC3).
- **Context:** `get_context_data` adds two keys:
  - `status_filter`: the `Goal.Status` member or `None`.
  - `status_choices`: `Goal.Status.choices`.
  - The template builds its links by looping over the choices, so a new status needs no template change.
- **Filter links:** a `<nav aria-label="Filter by status"><ul>` placed between the "New goal" link and the goal list. This is Pico's link-row idiom, with no custom CSS.
  - "All" points to `/goals/`; each status links to `/goals/?status=<value>`.
  - `aria-current="page"` goes on the active link only (AC6). It is the accessible way to mark the current filter.
- **Empty state:** `{% empty %}` shows "No goals with status <label>." when `status_filter` is set, and "No goals yet." otherwise.
- **AC8 is a characterization test:** `LoginRequiredMixin` already redirects every request to the view, query string included. The step-6 test is therefore expected to pass on its first run.
  - This is the one deliberate exception to "red first". It guards against a regression and is committed as `test(goal-list-filter): ...`.
- **AC2 and AC4 are folded into step 1's test:** step 1's test adds another user's goal with the same status and two same-status goals on different days. Scoping and order are then checked together with the filter itself.

## Steps
- [x] 1. `?status=<valid>` lists only the user's goals with that status, newest first.
  - Test: `src/apps/goals/tests/test_views.py`, parametrized over `planned`/`in_progress`/`done`.
  - Setup: one goal per status for "ada", a second goal in the requested status on a later day, and a "grace" goal in the requested status.
  - Asserts: only the matching titles appear, newest first, and grace's goal is absent.
  - Impl: `src/apps/goals/views.py`. `GoalListView.get_queryset` filters on `request.GET["status"]` when present.
  - Covers: AC1, AC2, AC4.
- [x] 2. A missing, empty or unknown `status` shows all goals with a 200.
  - Test: `test_views.py`, parametrized with ids `no-param` / `empty` / `unknown`, using `?status=foo`. Red because step 1 filters any non-empty value.
  - Impl: `views.py`. Add the `status_filter` helper, which validates against `Goal.Status`, and use it in `get_queryset`.
  - Covers: AC3.
- [x] 3. The list page shows the filter links "All" → `/goals/`, "Planned" → `/goals/?status=planned`, "In progress" → `/goals/?status=in_progress` and "Done" → `/goals/?status=done`, in that order.
  - Test: `test_views.py`.
  - Impl: `views.py` (`get_context_data` adds `status_choices`) and `goals/goal_list.html` (the `<nav>` link row).
  - Covers: AC5.
- [x] 4. The active filter link has `aria-current="page"`, and no other link has it.
  - Test: `test_views.py`, parametrized over `""` → All, `planned`, `in_progress`, `done` and `foo` → All.
  - Impl: `views.py` (context adds `status_filter`) and `goal_list.html` (conditional `aria-current`).
  - Covers: AC6.
- [ ] 5. When a valid filter matches nothing, the page shows "No goals with status <label>." and not "No goals yet.".
  - Test: `test_views.py`. "ada" has only a planned goal and requests `?status=done`.
  - The existing "No goals yet" test still covers the unfiltered case.
  - Impl: `goal_list.html` (`{% empty %}` branch).
  - Covers: AC7.
- [ ] 6. Anonymous `GET /goals/?status=done` redirects to login, and `next` carries the full path including the query.
  - This is a characterization test, expected green on the first run (see Design decisions).
  - Test: `test_views.py`.
  - Impl: none.
  - Covers: AC8.

## Coverage
| AC | Steps |
|----|-------|
| AC1 | 1 |
| AC2 | 1 |
| AC3 | 2 |
| AC4 | 1 |
| AC5 | 3 |
| AC6 | 4 |
| AC7 | 5 |
| AC8 | 6 |
