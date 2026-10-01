# Learning Companion

Track learning goals and sessions, attach reference material, and get AI-powered progress summaries and next steps. Built with Django as part of Recap Project 6 (see `instructions/`), developed through an AI-factory pipeline (see [docs/ai-factory-workflow.md](docs/ai-factory-workflow.md)).

## Stack

- Python 3.12+, Django 6.1, django-environ for configuration
- Server-rendered Django templates styled with Pico.css (CDN, no build step)
- SQLite locally; any database via `DATABASE_URL` (Postgres in Docker/CI)
- pytest + pytest-django for tests, ruff for linting

## Getting started

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp .env.example .env            # then adjust values
.venv/bin/python src/manage.py migrate
.venv/bin/python src/manage.py runserver
```

## Commands

| Task          | Command                                    |
|---------------|--------------------------------------------|
| Run tests     | `.venv/bin/pytest`                         |
| Lint          | `.venv/bin/ruff check .`                   |
| System checks | `.venv/bin/python src/manage.py check`     |
| Migrations    | `.venv/bin/python src/manage.py makemigrations` / `migrate` |
| New app       | `mkdir src/apps/<name> && .venv/bin/python src/manage.py startapp <name> src/apps/<name>` |

## Development workflow

Features are built one ticket at a time: `refine-ticket` → `plan-ticket` → `tdd-implement` → `final-review`, orchestrated by `factory-manager` from `work/backlog.md`. Hooks in `.claude/hooks/` enforce the phase gates.
