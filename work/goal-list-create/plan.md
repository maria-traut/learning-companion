# Plan: goal-list-create
## Research summary
- **Goal model** (`src/apps/goals/models.py`): `user` FK (`related_name="goals"`, CASCADE), `title` CharField(200), `description` TextField (required), `status` TextChoices `Goal.Status` (planned/"Planned", in_progress/"In progress", done/"Done"), default PLANNED; `created_at`/`updated_at`; `Meta.ordering = ["-created_at"]`; `__str__` → title. The goals app has no `urls.py`, `views.py`, `forms.py`, `templates/` or view tests yet, and `src/config/urls.py` doesn't include it (it has `admin/`, `accounts/`, `''` → pages).
- **Pattern to follow** (`src/apps/accounts/`): class-based views with `LoginRequiredMixin` and `SuccessMessageMixin` (`success_message`, `success_url = reverse_lazy(...)`). The `ModelForm` has an explicit `fields` list that never includes `user`. `app_name` is namespaced in the app `urls.py`. Templates live at `apps/<app>/templates/<app>/*.html`, use `{% extends "base.html" %}`, `{% block title %}X · Learning Companion{% endblock %}` and an `<h1>`, and have a single `<form method="post">` with no `action`, `{% csrf_token %}{{ form }}` and a submit button. Empty states use `{% empty %}`.
- **Nav** (`src/templates/base.html`): the second `<ul>` has `{% if user.is_authenticated %}` (profile link + logout form with an `action`) and `{% else %}` (Log in / Sign up). `tests/test_base_layout.py` matches `<nav>` exactly, so the `<nav>` tag itself must stay unchanged.
- **Auth settings**: `LOGIN_URL` is the default `/accounts/login/`. Messages render in `<section id="messages">`.
- **Test setup**: pytest-django with no conftest. Tests are module-level functions using the `client` / `django_user_model` fixtures, a local `user` fixture ("ada") with `PASSWORD = "correct-horse-battery-9"`, a second user "grace" created inline, and `client.force_login`. URLs are hard-coded strings. Regex helpers (`template_names`, `messages_text`, `nav_html`, `main_html`, `tag_attributes`, `form_field_names`) are defined per test file; today they exist only in `src/apps/accounts/tests/test_views.py`. Message checks use `follow=True` + `redirect_chain` + `messages_text`. Invalid input uses `@pytest.mark.parametrize(..., ids=[...])` and expects a 200 re-render with the error text and nothing saved. Goals in tests are created with `Goal.objects.create(user=..., title=..., description=...)`, and ordering is controlled by `Goal.objects.filter(pk=...).update(created_at=...)`.
- Single file run: `.venv/bin/pytest src/apps/goals/tests/test_views.py`.

## Design decisions
- **Views**: `GoalListView(LoginRequiredMixin, ListView)` and `GoalCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView)`, mirroring the accounts views.
- **Ownership**: the list's `get_queryset` returns `request.user.goals.all()`, so model ordering stays newest-first. `form_valid` sets `form.instance.user = request.user`. `GoalForm.Meta.fields = ["title", "description", "status"]`, so forged `user`/`id`/`pk` fields are never bound.
- **URLs**: `apps/goals/urls.py` with `app_name = "goals"` and names `list` (`""`) and `create` (`"new/"`), included at `goals/` in `config/urls.py`.
- **Created date**: rendered with Django's `date` filter at the default `DATE_FORMAT`. Tests compare it with `django.utils.formats.date_format(goal.created_at)`, so the test doesn't hard-code a locale.
- **Test helpers**: copy the needed regex helpers into `src/apps/goals/tests/test_views.py`, following the existing per-file convention. Extracting them into a shared conftest would mean refactoring the accounts tests, which this ticket doesn't cover.
- **Nav link**: goes inside the existing `{% if user.is_authenticated %}` block, before the profile link. Its tests live in the goals view tests.
- **Characterization tests (steps 9 and 10)**: these stay as separate steps, not folded into step 8, because each covers its own acceptance criterion and its own security or validation behaviour (AC10 forged ownership fields, AC11 invalid input). They're expected to pass on their first run. That behaviour comes from Django's form machinery: fields left out of `GoalForm.Meta.fields` are never bound, and ModelForm validation runs against the model's field rules. So no meaningful temporary break is available to see them red first; breaking it on purpose would mean sabotaging Django's form handling, not removing code this ticket adds. Each one is committed on its own as `test(goal-list-create): ...` and changes no production code. If one is unexpectedly red, that shows a real gap, and the minimal fix goes in that step.

## Steps
- [x] 1. Anonymous GET `/goals/` redirects to `/accounts/login/?next=/goals/` — test: `src/apps/goals/tests/test_views.py` — impl: `src/apps/goals/views.py` (`GoalListView`), `src/apps/goals/urls.py`, `src/config/urls.py`, `src/apps/goals/templates/goals/goal_list.html` — covers: AC1
- [x] 2. Logged-in GET `/goals/` returns 200 using `goals/goal_list.html` + `base.html`, with title "Goals · Learning Companion" — test: `src/apps/goals/tests/test_views.py` — impl: `goal_list.html` — covers: AC3
- [x] 3. The list shows each goal's title, status label and created date, newest first — test: `src/apps/goals/tests/test_views.py` — impl: `goal_list.html` — covers: AC4
- [x] 4. The list excludes another user's goals (Grace's goal titles don't appear in Ada's `main_html`) — test: `src/apps/goals/tests/test_views.py` — impl: `GoalListView.get_queryset` — covers: AC5
- [x] 5. The empty list shows an empty-state message — test: `src/apps/goals/tests/test_views.py` — impl: `goal_list.html` (`{% empty %}`) — covers: AC6
- [x] 6. Anonymous GET and POST to `/goals/new/` redirect to `/accounts/login/?next=/goals/new/`, and the POST creates no goal (parametrized over method) — test: `src/apps/goals/tests/test_views.py` — impl: `GoalCreateView` (bare), `urls.py` (`create`), `src/apps/goals/forms.py` (`GoalForm`), `goals/goal_form.html` — covers: AC2
- [x] 7. Logged-in GET `/goals/new/` returns 200 using `goals/goal_form.html` + `base.html`; the single POST form's fields are exactly `{title, description, status}`, and Planned is preselected — test: `src/apps/goals/tests/test_views.py` — impl: `goal_form.html`, `GoalForm` field list — covers: AC8
- [x] 8. A valid POST creates one goal owned by the user with the submitted values, redirects to `/goals/` and shows "Goal created." — test: `src/apps/goals/tests/test_views.py` — impl: `GoalCreateView.form_valid`, `success_url`, `success_message` — covers: AC9
- [x] 9. Characterization (expected green on first run, see Design decisions): forged `user`/`id`/`pk` POST fields are ignored; the new goal belongs to Ada and Grace's goal is unchanged — test: `src/apps/goals/tests/test_views.py` — impl: none expected — covers: AC10
- [x] 10. Characterization (expected green on first run, see Design decisions): an invalid POST (missing title, missing description, title of 201 chars, unknown status) re-renders `goals/goal_form.html` with 200 and the error text, and creates no goal (parametrized with ids) — test: `src/apps/goals/tests/test_views.py` — impl: none expected — covers: AC11
- [x] 11. The goal list links to `/goals/new/` — test: `src/apps/goals/tests/test_views.py` — impl: `goal_list.html` — covers: AC7
- [ ] 12. The nav shows a "Goals" link to `/goals/` for logged-in users and not for anonymous visitors (parametrized: the logged-in case fails first) — test: `src/apps/goals/tests/test_views.py` — impl: `src/templates/base.html` — covers: AC12

## Coverage
| AC | Steps |
|----|-------|
| AC1 | 1 |
| AC2 | 6 |
| AC3 | 2 |
| AC4 | 3 |
| AC5 | 4 |
| AC6 | 5 |
| AC7 | 11 |
| AC8 | 7 |
| AC9 | 8 |
| AC10 | 9 |
| AC11 | 10 |
| AC12 | 12 |
