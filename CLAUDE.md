# Learning Companion

Django app for tracking learning goals and sessions, attaching resources, and generating AI summaries/next steps. Requirements: `instructions/challenge.md`. Development follows the pipeline in `.claude/rules/` (workflow, TDD, git); the ticket queue is `work/backlog.md`, mirrored to GitHub issues and the project board (https://github.com/users/maria-traut/projects/5).

## Gitflow

`feature/<id>` / `fix/<id>` branch from `develop` → squash-merged PR into `develop` → `main` merged into `develop` (`chore(release): merge main into develop`) → promotion PR `develop` → `main` (merge commit). `main` and `develop` never take direct commits. Details: `.claude/rules/git.md`. Pipeline: `refine-ticket` → `plan-ticket` → `tdd-implement` → `final-review` → `release-ticket`, driven by `factory-manager`.

## Commands

Always use the project virtualenv (`.venv/`), never the system Python.

- Install: `.venv/bin/pip install -r requirements-dev.txt`
- Tests: `.venv/bin/pytest` (single file: `.venv/bin/pytest src/apps/goals/tests/test_views.py`)
- Lint: `.venv/bin/ruff check .`
- System checks: `.venv/bin/python src/manage.py check`
- Migrations: `.venv/bin/python src/manage.py makemigrations <app>` then `.venv/bin/python src/manage.py migrate`
- Dev server: `.venv/bin/python src/manage.py runserver`
- New app: `mkdir src/apps/<name> && .venv/bin/python src/manage.py startapp <name> src/apps/<name>`, then set `name = "apps.<name>"` in its `apps.py` and add `"apps.<name>"` to `INSTALLED_APPS`.

## Architecture

All application source code lives in `src/` (pytest adds it to the path via `pythonpath` in `pyproject.toml`). Repo-root files are tooling and config only.

- `src/manage.py` — Django management entry point.
- `src/config/` — Django project package (settings, root URLconf, WSGI/ASGI). Settings read env vars via django-environ from the repo-root `.env` (template: `.env.example`). Never hardcode secrets; `OPENAI_API_KEY` goes in `.env`.
- `src/apps/<name>/` — one Django app per domain area (e.g. `accounts`, `goals`, `learning_sessions`, `resources`, `ai`, `dashboard`), imported as `apps.<name>`. Learning sessions live in `learning_sessions`, not `sessions`, because that label clashes with `django.contrib.sessions`. Each app keeps its own `urls.py`, `templates/<name>/`, and `tests/`.
- `src/templates/` — project-wide templates (`base.html` layout, auth templates under `registration/`). UI is server-rendered with Pico.css from CDN; no JS build step.
- `src/static/` — project-wide static files.
- `tests/` — project-level tests (smoke tests, cross-app behaviour) at the repo root.
- Database: SQLite by default; `DATABASE_URL` switches it (Postgres in Docker/CI).

## Conventions

- Tests use pytest-django: plain `assert`, the `client` / `admin_client` / `django_user_model` fixtures, `@pytest.mark.django_db` for DB access. Name files `test_*.py`.
- Every view that shows user data must filter by `request.user` and be login-protected; test that another user's object returns 404.
- External APIs (OpenAI) are wrapped in a small service module and mocked in tests; tests never hit the network.
- Keep this file updated when commands or architecture change.
