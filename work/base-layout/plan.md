# Plan: base-layout

## Research summary
- Django 6.1.1, django-environ 0.14.0; pytest 9.1.1 + pytest-django 4.14.0; ruff 0.16.9 (line length 100, rules E/F/I/UP/B/DJ, migrations excluded). Python >= 3.12.
- pytest config in `pyproject.toml`: `DJANGO_SETTINGS_MODULE=config.settings`, `pythonpath=["src"]`, `testpaths=["tests","src"]`, `addopts="-q"`. No `conftest.py`.
- Test style (`tests/test_smoke.py`): plain functions with sentence-like names, the `client` fixture, act / blank line / plain `assert`. No classes.
- `TEMPLATES['DIRS'] = [BASE_DIR / 'templates']` (= `src/templates/`, currently empty), `APP_DIRS=True`, with the request/auth/messages context processors. `MessageMiddleware` is enabled and no `MESSAGE_*` settings are set.
- `src/config/urls.py` only has `admin/` and doesn't use `include()` yet. `src/apps/` has no apps.
- Per CLAUDE.md, each app is `apps.<name>` and has its own `urls.py`, `templates/<name>/` and `tests/`, and project-wide templates live in `src/templates/`. To create one: `mkdir src/apps/<name> && .venv/bin/python src/manage.py startapp <name> src/apps/<name>`, then set `name = "apps.<name>"` and add the app to `INSTALLED_APPS`.
- The write guard covers `src/` and `tests/`, templates included, so all of this ticket's files are written in `implementing`.

## Design decisions
- **New `pages` app** (`src/apps/pages/`) for the home view. Static, site-level pages don't belong to any domain app, and a later `dashboard` app gets its own ticket.
- **Home view = `TemplateView`** with `template_name = "pages/home.html"`, named URL `pages:home` at `""`, mounted via `include("apps.pages.urls")` in `config/urls.py`. It has no data and no auth.
- **`base.html` in `src/templates/`** as the project-wide layout. Blocks: `title` (default "Learning Companion") and `content`.
- **Pico.css v2 from jsDelivr, pinned to an exact version** (`https://cdn.jsdelivr.net/npm/@picocss/pico@2.1.1/css/pico.min.css`). The test asserts a `pico@<major>.<minor>.<patch>` href, so the version is pinned without the test tying itself to one release.
- **Messages container is a `<section>` with `id="messages"`**, rendered only when `messages` is non-empty. The id gives tests a stable hook.
- **Layout tests live in `tests/test_base_layout.py`** (project-level template). They render `base.html` with `render_to_string`. Message tests build a request with `RequestFactory`, attach session + message storage, and add a message through `django.contrib.messages`. Home-page tests live in `src/apps/pages/tests/test_views.py` and go through `client.get("/")`.

## Steps
- [x] 1. Anonymous `GET /` returns 200. Test: `src/apps/pages/tests/test_views.py`. Impl: `startapp pages` into `src/apps/pages/` (`apps.py` name, `INSTALLED_APPS`), `src/apps/pages/urls.py`, `src/apps/pages/views.py` (`HomeView`), `src/config/urls.py` (`include`), `src/apps/pages/templates/pages/home.html` (minimal). Covers: AC1.
- [x] 2. The home response uses both `pages/home.html` and `base.html`. Test: `src/apps/pages/tests/test_views.py`. Impl: `src/templates/base.html` (skeleton with `content` block), `home.html` extends it. Covers: AC2.
- [x] 3. `base.html` includes a stylesheet link to a pinned Pico.css CDN version. Test: `tests/test_base_layout.py`. Impl: `src/templates/base.html`. Covers: AC3.
- [x] 4. `base.html` renders a `<nav>` with a "Learning Companion" link to `/`. Test: `tests/test_base_layout.py`. Impl: `src/templates/base.html` (uses `{% url 'pages:home' %}`). Covers: AC4.
- [x] 5. `base.html` renders `<title>Learning Companion</title>` by default. Test: `tests/test_base_layout.py`. Impl: `src/templates/base.html` (`title` block). Covers: AC5.
- [x] 6. The home page's title is "Home · Learning Companion". Test: `src/apps/pages/tests/test_views.py`. Impl: `src/apps/pages/templates/pages/home.html` (overrides `title`). Covers: AC5.
- [x] 7. A message added through `django.contrib.messages` appears in the rendered `base.html`. Test: `tests/test_base_layout.py`. Impl: `src/templates/base.html` (messages loop in `#messages`). Covers: AC6.
- [x] 8. No `#messages` container is rendered when there are no messages. Test: `tests/test_base_layout.py`. Impl: `src/templates/base.html` (guard with `{% if messages %}`). Covers: AC6.
- [x] 9. `base.html` renders a `<footer>` containing "Learning Companion". Test: `tests/test_base_layout.py`. Impl: `src/templates/base.html`. Covers: AC7.
- [x] 10. The home page shows an `<h1>` and welcome text mentioning goals, sessions, resources and AI summaries. Test: `src/apps/pages/tests/test_views.py`. Impl: `src/apps/pages/templates/pages/home.html`. Covers: AC8.

Every step runs the full suite (`.venv/bin/pytest`) plus `.venv/bin/ruff check .` before committing. The existing smoke tests, system checks included, must stay green throughout. That covers AC9. After step 1 the system-check smoke test also validates the new app registration.

## Coverage
| AC | Steps |
|----|-------|
| AC1 | 1 |
| AC2 | 2 |
| AC3 | 3 |
| AC4 | 4 |
| AC5 | 5, 6 |
| AC6 | 7, 8 |
| AC7 | 9 |
| AC8 | 10 |
| AC9 | every step (full suite) |

## Review findings (from `review.md`, round 1)
Steps 11, 12, 13 and 15 only tighten tests that are already wrong or too weak (`.claude/rules/tdd.md`: fix a wrong test deliberately, as its own step). The code they check already behaves correctly, so they may be green as soon as they're written. Commit them as `test(base-layout): ...`. Before trusting each one, check that it *can* fail: temporarily break the behaviour it targets, watch it go red, then revert.

- [x] 11. A message added in one request appears inside `#messages` on the next page. Test: `tests/test_base_layout.py` with a test-only URLconf (`@pytest.mark.urls`) whose view calls `messages.success` and redirects to `/`; `client.get(..., follow=True)`. Impl: none expected. Covers: AC6 (finding 1).
- [x] 12. The home welcome assertions are scoped to `<main>`: a non-empty `<h1>`, plus goals, sessions, resources, AI summaries and next steps. Test: `src/apps/pages/tests/test_views.py` (replace the existing AC8 test). Impl: none expected. Covers: AC8 (finding 2).
- [x] 13. The Pico test finds the stylesheet `<link>` tag first, then asserts `rel="stylesheet"` and the pinned jsDelivr `href` separately, so attribute order doesn't matter. Test: `tests/test_base_layout.py` (replace the existing AC3 test). Impl: none expected. Covers: AC3 (finding 3).
- [ ] 14. The Pico `<link>` carries a `sha384-` `integrity` attribute and `crossorigin="anonymous"`. Test: `tests/test_base_layout.py`. Impl: `src/templates/base.html`, using the real sha384 of pico 2.1.1 `pico.min.css`. Covers: AC3 (finding 4).
- [ ] 15. Remove the unneeded `@pytest.mark.django_db` from the message tests. Test: `tests/test_base_layout.py`. Impl: none. Covers: — (finding 5). Skip this step if step 11's client-based test needs DB access; the in-request tests still don't.

Deferred, not planned: finding 6 (message tags / `role="status"`, goes with #2) and finding 7 (repo-wide quote style).
