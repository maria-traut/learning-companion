# Plan: profile-page

## Research summary
- **Django 6.1.1 behaviour (from the `.venv` source)**
  - **`LoginRequiredMixin`.** It redirects every anonymous request to `LOGIN_URL` with `?next=<full path>`, and handles GET and POST the same way. `next` is encoded with `safe="/"`, so the targets are `/accounts/login/?next=/accounts/profile/` and `/accounts/login/?next=/accounts/profile/edit/`. `LoginRequiredMiddleware` exists but isn't enabled, so the views need the mixin. `LOGIN_URL` is the default `/accounts/login/`.
  - **`UpdateView` / `DetailView`.** Override `get_object(self, queryset=None)`, and no pk/slug is needed in the URL. `ModelFormMixin.form_valid` calls `form.save()` with `commit=True`, which saves the M2M too, then redirects to `get_success_url()`. Without `success_url`, it raises `ImproperlyConfigured` because `Profile` has no `get_absolute_url`. `SuccessMessageMixin` goes before `UpdateView` and formats its message with `%`.
  - **`CheckboxSelectMultiple`.** It renders a `<fieldset>`/`<legend>Focus areas:</legend>` and one `<input type="checkbox" name="focus_areas" value="<pk>" id="id_focus_areas_<n>">` per option, with bare `checked` on ticked boxes, labelled by `str()` and ordered by name. With an empty queryset it renders the fieldset and an empty `<div id="id_focus_areas">` with no inputs.
  - **Error texts.**
    - Too long: `Ensure this value has at most 100 characters (it has 101).`
    - Unknown pk: `Select a valid choice. 999 is not one of the available choices.`
    - Values are autoescaped.
  - **The `get_or_create` cache.** `ReverseOneToOneDescriptor` caches a miss: once `request.user.profile` has raised, it keeps raising for that request. `Profile.objects.get_or_create(user=request.user)` creates the row without problems, so the view must use the object it returns, not `request.user.profile`. `force_login` loads a fresh user on every request, so tests that delete a profile first see no stale cache in the view. Inside the test itself, read profiles back with `Profile.objects.get(user=...)`.
- **Project state (after #3)**
  - **Models:** `Profile` (`name` and `cohort` are CharField(100, blank); `focus_areas` is an M2M to `FocusArea`, blank, `related_name="profiles"`) and `FocusArea` (unique `name`, ordered by name).
  - **Profile creation:** the `post_save` signal creates profiles. No `FocusArea` rows are seeded.
  - **Existing views and URLs:** `apps.accounts` has `SignUpView`, `LoginView` and `LogoutView`. There's no `forms.py` and no app `templates/` dir yet. `urls.py` has `app_name = "accounts"`, mounted at `accounts/`, and `/accounts/profile/` is free.
  - **`base.html` nav:** for a logged-in user it shows `<li>{{ user.get_username }}</li>` and a logout `<form method="post" action="{% url 'accounts:logout' %}">`. Anonymous users get Log in and Sign up links. Messages render as `<section id="messages" role="status">` with one `<article>` per message. No existing nav or layout test breaks if the username becomes a link.
  - **Templates:**
    - Every page extends `base.html`, with `{% block title %}<Page> · Learning Companion{% endblock %}` and an `<h1>`.
    - Forms are written as `<form method="post">{% csrf_token %}{{ form }}<button type="submit">…</button></form>`.
    - Per CLAUDE.md, app templates go in `src/apps/<app>/templates/<app>/`.
  - **Code style:** double quotes, isort imports, no docstrings, comments or type hints. Ruff DJ rules apply: DJ006/DJ007 mean explicit `fields`, no `exclude` or `"__all__"`.
- **Tests**
  - `src/apps/accounts/tests/test_views.py` already has `PASSWORD`, the `user` fixture (ada) and the helpers `template_names`, `messages_text`, `nav_html` and `signup_data`.
  - Logged-in tests use `client.force_login`. Paths are hard-coded strings, and HTML is checked with regex.
  - Removing a user's profile in a test is done with `user.profile.delete()`, as in `test_admin.py`.
  - The suite currently has 57 passing tests.

## Design decisions
- **Two views in `src/apps/accounts/views.py`, both id-free:**
  - `ProfileView(LoginRequiredMixin, DetailView)` at `profile/`, named `accounts:profile`, with template `accounts/profile_detail.html`.
  - `ProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView)` at `profile/edit/`, named `accounts:profile_edit`, with template `accounts/profile_form.html`, `form_class = ProfileForm`, `success_url = reverse_lazy("accounts:profile")` and `success_message = "Profile updated."`.
- **The object is always the requester's own profile.** At first `get_object` returns `self.request.user.profile` (steps 2 and 6). Step 14 replaces it with a shared `OwnProfileMixin.get_object` that returns `Profile.objects.get_or_create(user=self.request.user)[0]`. Neither view ever looks a profile up from request data, which is what makes AC3 and AC7 hold.
- **`ProfileForm(forms.ModelForm)`** goes in a new `src/apps/accounts/forms.py`, with `Meta.fields = ["name", "cohort", "focus_areas"]` and `widgets = {"focus_areas": forms.CheckboxSelectMultiple}`. There's no `user` field, so a forged `user` in the POST is ignored by the form.
- **Templates in `src/apps/accounts/templates/accounts/`:**
  - The detail page uses a `<dl>`: Username, Name, Cohort and Focus areas, as a `<ul>` of names. Empty values show "Not set yet", and no focus areas shows "No focus areas yet". It links to the edit page with "Edit profile".
  - The form page uses the project's form pattern. When `form.fields.focus_areas.queryset` is empty it shows "No focus areas available yet."
- **Nav:** the username becomes `<a href="{% url 'accounts:profile' %}">{{ user.get_username }}</a>` inside the authenticated branch only.
- **Tests** go in `src/apps/accounts/tests/test_views.py`, next to the existing view and nav tests and reusing their helpers. Moving the helpers into a `conftest.py` is still a deferred follow-up from #3.
- **Characterization steps (3, 7, 9, 11, 12).** These cover behaviour that follows from earlier steps (own-object lookup, explicit form fields, ModelForm validation and M2M replacement), so their tests may pass as soon as they're written. Each one is checked by temporarily breaking the behaviour, watching the test go red, and reverting. They are committed as `test(profile-page): ...`.
- **Red reasons that are exceptions, not assertions (steps 8 and 14).** The behaviour under test is the missing piece itself. Before step 8 there's no `success_url`, so the view raises `ImproperlyConfigured`. Before step 14 a user without a profile raises `RelatedObjectDoesNotExist`. These are the expected failures, not syntax or import errors; each is named in the step so it can be confirmed when the test is run.

## Steps
- [x] 1. An anonymous `GET /accounts/profile/` redirects (302) to `/accounts/login/?next=/accounts/profile/`. Test: `src/apps/accounts/tests/test_views.py`. Impl: `views.py` (`ProfileView(LoginRequiredMixin, DetailView)`, a bare shell), `urls.py` (`profile/`, name `profile`). Covers: AC1.
- [x] 2. A logged-in `GET /accounts/profile/` returns 200, renders `accounts/profile_detail.html` and `base.html`, and shows the user's username, name, cohort and focus-area names. In the test, ada's profile is set to "Ada Lovelace" / "Web Dev Berlin 2026-03" with two focus areas. Test: `test_views.py`. Impl: `ProfileView.get_object` (`self.request.user.profile`), `src/apps/accounts/templates/accounts/profile_detail.html`. Covers: AC2.
- [x] 3. *(characterization)* With ada and grace holding different names, cohorts and focus areas, each user's profile page contains their own values and none of the other's. Test: `test_views.py`. Impl: none expected. Verify by temporarily returning another user's profile from `get_object`. Covers: AC3.
- [x] 4. An anonymous `GET` and `POST` to `/accounts/profile/edit/` redirect to `/accounts/login/?next=/accounts/profile/edit/`. Parametrized by method; the POST case also asserts that ada's profile is unchanged. Test: `test_views.py`. Impl: `views.py` (`ProfileUpdateView(LoginRequiredMixin, UpdateView)`, a bare shell), `urls.py` (`profile/edit/`, name `profile_edit`). Covers: AC1.
- [ ] 5. The profile page has a link to `/accounts/profile/edit/`. Test: `test_views.py`. Impl: `profile_detail.html`. Covers: AC4.
- [ ] 6. A logged-in `GET /accounts/profile/edit/` returns 200 and renders `accounts/profile_form.html`. Its form is pre-filled with the current `name` and `cohort`, has one `focus_areas` checkbox per existing `FocusArea`, and the user's current focus areas are `checked` (three areas exist, two are ticked). Test: `test_views.py`. Impl: `src/apps/accounts/forms.py` (`ProfileForm`), `ProfileUpdateView` (`form_class`, `get_object`), `src/apps/accounts/templates/accounts/profile_form.html`. Covers: AC5.
- [ ] 7. *(characterization)* The edit form has exactly the field names `{"name", "cohort", "focus_areas"}`, ignoring `csrfmiddlewaretoken`. Test: `test_views.py`. Impl: none expected. Verify by temporarily adding `"user"` to `ProfileForm.Meta.fields`. Covers: AC7.
- [ ] 8. A valid `POST` to `/accounts/profile/edit/` saves the new `name`, `cohort` and focus areas, replacing a previous set (start `{django, sql}`, post `{sql, testing}`), and redirects (302) to `/accounts/profile/`. Expected red: `ImproperlyConfigured` (no success URL). Test: `test_views.py`. Impl: `ProfileUpdateView.success_url`. Covers: AC6.
- [ ] 9. *(characterization)* A `POST` that ticks no focus areas clears the user's existing focus areas. Test: `test_views.py`. Impl: none expected. Verify by temporarily making `focus_areas` required in `ProfileForm`. Covers: AC6.
- [ ] 10. Following the redirect after a valid save shows "Profile updated" inside `#messages` on the profile page. Test: `test_views.py`. Impl: `ProfileUpdateView` (`SuccessMessageMixin`, `success_message`). Covers: AC6.
- [ ] 11. *(characterization)* A `POST` as ada that also sends `user=<grace.pk>` plus an unknown extra field updates only ada's profile. Ada's profile keeps `user == ada`, and grace's profile (name, cohort, focus areas) is unchanged. Test: `test_views.py`. Impl: none expected. Verify by temporarily adding `"user"` to `ProfileForm.Meta.fields`. Covers: AC7.
- [ ] 12. *(characterization)* An invalid `POST` re-renders `accounts/profile_form.html` with 200 and the matching error, and saves nothing. Parametrized with `ids=` over: a 101-character `name`, a 101-character `cohort`, and a focus-area id that doesn't exist. Test: `test_views.py`. Impl: none expected. Verify the `name` and `cohort` cases by temporarily declaring those form fields without `max_length`; SQLite doesn't enforce the column length, so the long value saves and the test goes red. The focus-area case is checked by its error-text assertion only. The rejection happens in Django's `ModelMultipleChoiceField` before any hook in our code runs, so there is no small break to make here. Covers: AC8.
- [ ] 13. With no `FocusArea` rows, the edit page shows "No focus areas available yet", and a `POST` of `name` and `cohort` alone saves them and redirects. Test: `test_views.py`. Impl: `profile_form.html` (conditional on the focus-area queryset). Covers: AC9.
- [ ] 14. A logged-in user whose profile row was deleted gets exactly one empty profile when opening either page (200). Parametrized over `/accounts/profile/` and `/accounts/profile/edit/`. Expected red: `RelatedObjectDoesNotExist`. Test: `test_views.py`. Impl: `views.py` (`OwnProfileMixin.get_object` using `get_or_create`, used by both views in place of their own `get_object`). Covers: AC10.
- [ ] 15. For a logged-in user, the nav contains `<a href="/accounts/profile/">ada</a>`. The anonymous nav contains no `/accounts/profile/`; this part is already true, and checked by a temporary break. Test: `test_views.py`. Impl: `src/templates/base.html`. Covers: AC11.

## Coverage
| AC | Steps |
|---|---|
| AC1 anonymous redirected to login, POST changes nothing | 1, 4 |
| AC2 own username, name, cohort, focus areas shown | 2 |
| AC3 only own data shown | 3 |
| AC4 link to edit page | 5 |
| AC5 pre-filled form, one checkbox per focus area, own ones checked | 6 |
| AC6 valid save replaces values, redirects, "Profile updated" | 8, 9, 10 |
| AC7 exactly three editable fields; forged/extra values can't touch other profiles | 7, 11 |
| AC8 invalid input re-renders with error, saves nothing | 12 |
| AC9 no focus areas available | 13 |
| AC10 missing profile created on the spot | 14 |
| AC11 nav username links to profile, anonymous has no link | 15 |
