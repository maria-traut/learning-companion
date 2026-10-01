# Plan: auth

## Research summary
- **Django 6.1.1 auth (from `.venv` source)**
  - `LoginView`: `template_name="registration/login.html"`, `redirect_authenticated_user=False` by default (when True, an authenticated GET redirects to the success URL and raises `ValueError` if that is the login URL itself). `next` is read from POST, then GET, and validated with `url_has_allowed_host_and_scheme`. An unsafe value falls back to `LOGIN_REDIRECT_URL`, whose default is `/accounts/profile/`. `form_valid` calls `auth_login` and then redirects.
  - `LogoutView`: `http_method_names = ["post", "options"]`, so GET returns 405. It redirects to `next_page`, then `LOGOUT_REDIRECT_URL`, and otherwise renders `registration/logged_out.html`.
  - `django.contrib.auth.urls` has no sign-up route.
  - `UserCreationForm` fields are `username`, `password1`, `password2`. Error texts:
    - mismatched passwords: "The two password fields didn’t match." (curly apostrophe) on `password2`
    - password validators: errors on `password2`
    - duplicate username, checked case-insensitively: "A user with that username already exists."
    - There is no `usable_password` field on this form.
  - `SuccessMessageMixin` adds `messages.success(get_success_message(cleaned_data))` after `super().form_valid`. With `CreateView`, `cleaned_data` includes the passwords, so never interpolate it.
  - `user_logged_in` and `user_logged_out` signals exist. `auth_logout` flushes the session.
- **Project state**
  - The only app is `apps.pages` (`pages:home` at `/`).
  - `src/config/urls.py` has `admin/` and `include("apps.pages.urls")`.
  - There are no `LOGIN_*`, `LOGOUT_*` or `MESSAGE_*` settings. Message storage is the default `FallbackStorage` (cookie first).
  - `base.html` nav has one `<ul>` with the brand link. Messages render as `<section id="messages">` containing one `<article>` per message, only when there are messages.
  - Per CLAUDE.md, auth templates go under `src/templates/registration/`.
- **Test conventions** (`tests/test_base_layout.py`, `src/apps/pages/tests/test_views.py`)
  - Plain functions using the `client`/`rf` fixtures; arrange / blank line / assert.
  - Regex style: find the container with `re.search(r"<tag[^>]*>(.*?)</tag>", html, re.DOTALL)`, then assert inside the match.
  - Helpers: `request_with_messages(rf)`, `pico_link_tag`, and a test-only URLconf via `@pytest.mark.urls(__name__)`.
  - No `django_db` unless needed; user creation and login need it.
- **Lessons from #1** (`work/base-layout/review.md`)
  - Write all `src/` and `tests/` files with the Write/Edit tools so the post-write hook logs red/green.
  - Extract a messages-container helper the next time those tests change.
  - Add `django_db` if message storage ends up needing the session.

## Design decisions
- **New `accounts` app** (`src/apps/accounts/`, namespace `accounts`), mounted at `accounts/`: `accounts:signup` (`/accounts/signup/`), `accounts:login` (`/accounts/login/`), `accounts:logout` (`/accounts/logout/`). CLAUDE.md already names `accounts` as the auth domain app, and #3's profile model will live there too.
- **Built-in views, thinly subclassed**, kept in `src/apps/accounts/views.py`:
  - `LoginView` with `redirect_authenticated_user = True`. It overrides `form_valid` to add `Welcome, <user.get_username()>` (the stored username, not the raw input).
  - `LogoutView` subclass: after `super().post()`, adds `messages.info("You have been logged out.")`. The message is added after the session flush, so it survives.
  - `SignUpView(SuccessMessageMixin, CreateView)` with `form_class=UserCreationForm`, `success_url=reverse_lazy("accounts:login")` and a fixed message "Account created. Please log in." Its `dispatch` redirects authenticated users to `LOGIN_REDIRECT_URL`. This view is the single place #3 extends for profile creation.
- **Settings**: `LOGIN_URL = "accounts:login"`, `LOGIN_REDIRECT_URL = "pages:home"`, `LOGOUT_REDIRECT_URL = "pages:home"`. Use URL names, not hard-coded paths.
- **Templates**: `src/templates/registration/login.html` and `src/templates/registration/signup.html`. Both extend `base.html`, have their own `title` block, and render a `<form method="post">` with `{% csrf_token %}` and `{{ form }}`. `{{ form }}` renders field and non-field errors without extra markup.
- **Nav**: a second `<ul>` in `base.html`'s `<nav>`. If anonymous: "Log in" and "Sign up" links. If authenticated: the username and a `<form method="post" action="{% url 'accounts:logout' %}">` with `{% csrf_token %}` and a "Log out" button.
- **Messages markup (AC13)**: `<section id="messages" role="status">`, and each message is `<article class="{{ message.tags }}">`.
- **Tests**:
  - Behaviour of the accounts views goes in `src/apps/accounts/tests/test_views.py` (client, `django_db`, `django_user_model`). The nav login state is tested there too through `client.get("/")`, because it needs real users.
  - Message markup tests stay in `tests/test_base_layout.py`.
  - Shared test credentials use a password strong enough for the validators (e.g. `"correct-horse-battery-9"`).
- **Characterization steps** (6, 9, 10, 13): behaviour that Django already provides once the earlier steps exist, so the test may be green as soon as it's written. These tests are still required because they pin the AC. Each one is checked by temporarily breaking the behaviour, watching the test go red and reverting, as in #1 round 2. Commit them as `test(auth): ...`.

## Steps
- [x] 1. An anonymous `GET /accounts/signup/` returns 200, renders `registration/signup.html` and `base.html`, and the page has `username`, `password1` and `password2` inputs. Test: `src/apps/accounts/tests/test_views.py`. Impl: `startapp accounts` into `src/apps/accounts/` (`apps.py` name `apps.accounts`, add to `INSTALLED_APPS`; replace `tests.py` with a `tests/` package; drop the unused `admin.py`/`models.py`/`migrations` stubs as in #1), `src/apps/accounts/urls.py`, `views.py` (`SignUpView`), `src/config/urls.py` (`path("accounts/", include("apps.accounts.urls"))`), `src/templates/registration/signup.html`. Covers: AC1.
- [x] 2. An anonymous `GET /accounts/login/` returns 200, renders `registration/login.html` and `base.html`, and the page has `username` and `password` inputs. Test: `src/apps/accounts/tests/test_views.py`. Impl: `views.py` (`LoginView` subclass), `urls.py`, `src/templates/registration/login.html`. Covers: AC4.
- [x] 3. *(characterization, revised during implementation)* `resolve_url(settings.LOGIN_URL)` equals `reverse("accounts:login")`. Test: `src/apps/accounts/tests/test_views.py`. Impl: none. Django's default `LOGIN_URL` is `/accounts/login/`, which is already the route from step 2, so the test was green when first written. Setting `LOGIN_URL` explicitly would be untested production code. Verified by temporarily moving the login route, which turns the test red. Covers: AC12.
- [x] 4. A valid sign-up POST creates the user, redirects to `/accounts/login/`, and leaves the client anonymous (`"_auth_user_id" not in client.session`). Test: `src/apps/accounts/tests/test_views.py`. Impl: `SignUpView` (`success_url`). Covers: AC2.
- [x] 5. Following the sign-up redirect shows "Account created" inside `#messages` on the login page. Test: `src/apps/accounts/tests/test_views.py`. Impl: `SignUpView` (`SuccessMessageMixin`). Covers: AC2.
- [x] 6. *(characterization)* Invalid sign-ups re-render the form (200) with the matching error and create no user. Parametrized over: mismatched passwords, a username that is taken (case-insensitive), and a password the validators reject (e.g. `"12345678"`). Test: `src/apps/accounts/tests/test_views.py`. Impl: none expected. Covers: AC3.
- [x] 7. A valid login POST redirects to `/` and authenticates the client. Test: `src/apps/accounts/tests/test_views.py`. Impl: `src/config/settings.py` (`LOGIN_REDIRECT_URL`). Covers: AC5.
- [x] 8. After login, the home page shows "Welcome, <username>" inside `#messages`. Test: `src/apps/accounts/tests/test_views.py`. Impl: `LoginView` subclass `form_valid`. Covers: AC5.
- [x] 9. *(characterization)* A login POST with `next=/some/safe/path/` redirects there, and `next=https://evil.example.com/` redirects to `/`. Test: `src/apps/accounts/tests/test_views.py`. Impl: none expected. Covers: AC6.
- [x] 10. *(characterization)* A login POST with a wrong password returns 200 with the form error, and the client stays anonymous. Test: `src/apps/accounts/tests/test_views.py`. Impl: none expected. Covers: AC7.
- [x] 11. For a logged-in client, `POST /accounts/logout/` logs out and redirects to `/`. Test: `src/apps/accounts/tests/test_views.py`. Impl: `views.py` (`LogoutView` subclass), `urls.py`, `src/config/settings.py` (`LOGOUT_REDIRECT_URL`). Covers: AC8.
- [x] 12. After logout, the home page shows "You have been logged out" inside `#messages`. Test: `src/apps/accounts/tests/test_views.py`. Impl: `LogoutView` subclass `post`. Covers: AC8.
- [ ] 13. *(characterization)* `GET /accounts/logout/` returns 405, and the client stays logged in. Test: `src/apps/accounts/tests/test_views.py`. Impl: none expected. Covers: AC8.
- [ ] 14. For an anonymous visitor, the `<nav>` on `/` has links to `/accounts/login/` ("Log in") and `/accounts/signup/` ("Sign up") and no logout form. Test: `src/apps/accounts/tests/test_views.py`. Impl: `src/templates/base.html`. Covers: AC9.
- [ ] 15. For a logged-in user, the `<nav>` on `/` shows the username and a `<form method="post" action="/accounts/logout/">` containing a `csrfmiddlewaretoken` input and a "Log out" button, and has no login or sign-up links. Test: `src/apps/accounts/tests/test_views.py`. Impl: `src/templates/base.html`. Covers: AC10.
- [ ] 16. A logged-in `GET /accounts/login/` redirects to `/`. Test: `src/apps/accounts/tests/test_views.py`. Impl: `LoginView` subclass (`redirect_authenticated_user = True`). Covers: AC11.
- [ ] 17. A logged-in `GET /accounts/signup/` redirects to `/`. Test: `src/apps/accounts/tests/test_views.py`. Impl: `SignUpView.dispatch`. Covers: AC11.
- [ ] 18. Each rendered message `<article>` includes its `message.tags` value as a CSS class: `success` for `messages.success`, `info` for `messages.info`, and an `extra_tags` value is included too (e.g. `messages.info(..., extra_tags="note")` gives both `note` and `info` in the class list). Test: `tests/test_base_layout.py`. Refactor first, on green: extract a `messages_container(html)` helper for the duplicated `#messages` regex (base-layout review finding 2). Impl: `src/templates/base.html`. Covers: AC13.
- [ ] 19. The `#messages` container has `role="status"`, so assistive technologies announce messages. Test: `tests/test_base_layout.py`. Impl: `src/templates/base.html`. Covers: AC13.

Every step runs `.venv/bin/pytest` and `.venv/bin/ruff check .` before committing. The existing 14 tests must stay green. If any message test errors on DB access, because message storage fell back to the session, add `@pytest.mark.django_db` to that test (base-layout review finding 1).

## Coverage
| AC | Steps |
|----|-------|
| AC1 | 1 |
| AC2 | 4, 5 |
| AC3 | 6 |
| AC4 | 2 |
| AC5 | 7, 8 |
| AC6 | 9 |
| AC7 | 10 |
| AC8 | 11, 12, 13 |
| AC9 | 14 |
| AC10 | 15 |
| AC11 | 16, 17 |
| AC12 | 3 |
| AC13 | 18, 19 |
