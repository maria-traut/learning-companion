# Plan: goal-detail
## Research summary
- **Django 6.1.1.**
  - `SingleObjectMixin.get_object()` filters `get_queryset()` by the `pk` URL kwarg and raises `Http404` when nothing matches. `get_queryset` is the override point for scoping objects to their owner.
  - `UpdateView` uses `template_name_suffix = "_form"`, so it defaults to `goals/goal_form.html` and shares the template with create.
  - On POST, `DeleteView` (`BaseDeleteView(DeletionMixin, FormMixin, BaseDetailView)`) calls `form_valid()`. `SuccessMessageMixin` therefore works when it's listed before `DeleteView`, and `self.object` is still readable after the delete.
  - `DeleteView` uses `template_name_suffix = "_confirm_delete"`, so it defaults to `goals/goal_confirm_delete.html`. The context object name is `goal`.
  - `UpdateView`'s default success URL is `object.get_absolute_url()`.
- **Existing goals app** (from goal-list-create):
  - `GoalListView(LoginRequiredMixin, ListView)` uses `get_queryset` → `request.user.goals.all()`.
  - `GoalCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView)` uses `GoalForm` (fields `title`, `description`, `status`), `template_name = "goals/goal_form.html"`, `success_url = reverse_lazy("goals:list")`, and sets `form.instance.user` in `form_valid`.
  - `urls.py` has `app_name = "goals"` with routes `list` (`""`) and `create` (`"new/"`).
  - `goal_form.html` hard-codes the title "New goal · Learning Companion" and `<h1>New goal</h1>`.
  - In `goal_list.html`, each item shows a plain `<strong>{{ goal.title }}</strong>` with no link.
  - `Goal` has no `get_absolute_url`.
- **No delete or 404 precedent.** No `DeleteView`, confirm template or `status_code == 404` test exists anywhere yet. There is no custom `404.html`. The closest POST-only pattern is the logout form in `base.html`.
- **Test setup.**
  - `src/apps/goals/tests/test_views.py` (269 lines) already has:
    - the `user` fixture ("ada") and the `PASSWORD` and `DESCRIPTION` constants;
    - the helpers `template_names`, `messages_text`, `nav_html`, `main_html`, `tag_attributes`, `own_post_form`, `form_field_names` and `create_goal(user, title, status=..., day=1)`.
  - Conventions:
    - hard-coded URLs and `client.force_login`;
    - `follow=True` + `redirect_chain` + `messages_text` for messages;
    - `@pytest.mark.parametrize(..., ids=[...])` for variants;
    - "grace" as the second user, created inline.
  - Single file run: `.venv/bin/pytest src/apps/goals/tests/test_views.py`.

## Design decisions
- **Ownership scoping**:
  - A shared `OwnGoalMixin(LoginRequiredMixin)` in `views.py` overrides `get_queryset()` → `self.request.user.goals.all()`.
  - Detail, update and delete views all use it. Another user's goal and a missing pk then go down the same `Http404` path, so the URL doesn't reveal whether a goal exists.
  - `LoginRequiredMixin` runs first, so anonymous visitors are redirected before any lookup.
- **Views**: `GoalDetailView(OwnGoalMixin, DetailView)`, `GoalUpdateView(OwnGoalMixin, SuccessMessageMixin, UpdateView)` with `form_class = GoalForm`, and `GoalDeleteView(OwnGoalMixin, SuccessMessageMixin, DeleteView)` with `success_url = reverse_lazy("goals:list")`.
- **URLs**: `<int:pk>/` → `detail`, `<int:pk>/edit/` → `update`, `<int:pk>/delete/` → `delete`.
- **`Goal.get_absolute_url()`** returns `reverse("goals:detail", args=[self.pk])`. It's the idiomatic success URL for `UpdateView`, and templates can use it for links. It needs no migration.
- **Shared form template**: `goal_form.html` shows "Edit goal" (heading and page title) when editing an existing goal and "New goal" otherwise, so the edit page doesn't call itself "New goal".
- **404 tests** are parametrized over `other-user` and `missing`, one test per view (GET and POST where the view accepts POST). The `other-user` case is the one that's red first; the `missing` case already returns 404 through Django's `get_object`. Each 404 step comes right after its view first exists, so no commit leaves a view unscoped for longer than one red–green cycle.
- **Characterization tests (steps 10 and 11)**: these mirror goal-list-create's steps 9 and 10 for the edit form, and stay separate steps because each covers its own acceptance criterion (AC8 forged ownership fields, AC9 invalid input).
  - They're expected to pass on their first run. Fields left out of `GoalForm.Meta.fields` are never bound, the owner comes from the scoped queryset, and ModelForm validation applies the model's field rules.
  - So no meaningful temporary break is available to see them red first.
  - Each is committed on its own as `test(goal-detail): ...` with no production code. If one is unexpectedly red, that's a real gap, and the minimal fix goes in that step.
- **Anonymous redirect tests** use a real goal owned by Ada and assert the goal is unchanged or still exists after the POST variants.

## Steps
- [x] 1. Anonymous GET `/goals/<pk>/` redirects to `/accounts/login/?next=/goals/<pk>/` — test: `src/apps/goals/tests/test_views.py` — impl: `GoalDetailView` (bare, `LoginRequiredMixin`), `urls.py` (`detail`) — covers: AC1
- [ ] 2. Owner GET `/goals/<pk>/` returns 200 using `goals/goal_detail.html` + `base.html`, with title "<goal title> · Learning Companion" — test: `src/apps/goals/tests/test_views.py` — impl: `src/apps/goals/templates/goals/goal_detail.html` — covers: AC2
- [ ] 3. Detail returns 404 for another user's goal and for a missing pk (parametrized `other-user` / `missing`) — test: `src/apps/goals/tests/test_views.py` — impl: `OwnGoalMixin.get_queryset`, applied to `GoalDetailView` — covers: AC12, AC13
- [ ] 4. Detail page shows title, description, status label, created date and updated date — test: `src/apps/goals/tests/test_views.py` — impl: `goal_detail.html` — covers: AC3
- [ ] 5. Each goal title in the list links to its detail page — test: `src/apps/goals/tests/test_views.py` — impl: `goal_list.html` — covers: AC5
- [ ] 6. Anonymous GET and POST to `/goals/<pk>/edit/` redirect to login, and the goal is unchanged (parametrized over method) — test: `src/apps/goals/tests/test_views.py` — impl: `GoalUpdateView` (bare), `urls.py` (`update`) — covers: AC1
- [ ] 7. Owner GET `/goals/<pk>/edit/` returns 200 using `goals/goal_form.html`; the single POST form has exactly `{title, description, status}`, pre-filled with the goal's values, under the heading "Edit goal" — test: `src/apps/goals/tests/test_views.py` — impl: `GoalUpdateView` (`form_class`, `template_name`), `goal_form.html` heading/title — covers: AC6
- [ ] 8. Edit GET and POST return 404 for another user's goal and a missing pk, and the other user's goal is unchanged (parametrized `other-user`/`missing` × `get`/`post`) — test: `src/apps/goals/tests/test_views.py` — impl: `GoalUpdateView` uses `OwnGoalMixin` — covers: AC12, AC13
- [ ] 9. A valid edit POST saves title, description and status, keeps the owner, redirects to `/goals/<pk>/` and shows "Goal updated." — test: `src/apps/goals/tests/test_views.py` — impl: `Goal.get_absolute_url` (`src/apps/goals/models.py`), `SuccessMessageMixin` + `success_message` on `GoalUpdateView` — covers: AC7
- [ ] 10. Characterization (expected green on first run, see Design decisions): forged `user`/`id`/`pk` fields in the edit POST are ignored; the same goal is updated and stays Ada's, and Grace's goal is unchanged — test: `src/apps/goals/tests/test_views.py` — impl: none expected — covers: AC8
- [ ] 11. Characterization (expected green on first run, see Design decisions): an invalid edit POST (missing title, missing description, 201-char title, unknown status) re-renders `goals/goal_form.html` with 200 and the error, and leaves the goal unchanged (parametrized with ids) — test: `src/apps/goals/tests/test_views.py` — impl: none expected — covers: AC9
- [ ] 12. Anonymous GET and POST to `/goals/<pk>/delete/` redirect to login, and the goal still exists (parametrized over method) — test: `src/apps/goals/tests/test_views.py` — impl: `GoalDeleteView` (bare), `urls.py` (`delete`) — covers: AC1
- [ ] 13. Owner GET `/goals/<pk>/delete/` returns 200 using `goals/goal_confirm_delete.html` + `base.html`, asks to confirm deleting the goal by title, and has a single POST form — test: `src/apps/goals/tests/test_views.py` — impl: `src/apps/goals/templates/goals/goal_confirm_delete.html` — covers: AC10
- [ ] 14. Delete GET and POST return 404 for another user's goal and a missing pk, and the other user's goal still exists (parametrized `other-user`/`missing` × `get`/`post`) — test: `src/apps/goals/tests/test_views.py` — impl: `GoalDeleteView` uses `OwnGoalMixin` — covers: AC12, AC13
- [ ] 15. Owner POST to `/goals/<pk>/delete/` deletes the goal, redirects to `/goals/` and shows "Goal deleted." — test: `src/apps/goals/tests/test_views.py` — impl: `success_url`, `SuccessMessageMixin` + `success_message` on `GoalDeleteView` — covers: AC11
- [ ] 16. Detail page links to `/goals/<pk>/edit/` and `/goals/<pk>/delete/` — test: `src/apps/goals/tests/test_views.py` — impl: `goal_detail.html` — covers: AC4

## Coverage
| AC | Steps |
|----|-------|
| AC1 | 1, 6, 12 |
| AC2 | 2 |
| AC3 | 4 |
| AC4 | 16 |
| AC5 | 5 |
| AC6 | 7 |
| AC7 | 9 |
| AC8 | 10 |
| AC9 | 11 |
| AC10 | 13 |
| AC11 | 15 |
| AC12 | 3, 8, 14 |
| AC13 | 3, 8, 14 |
