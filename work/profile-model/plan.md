# Plan: profile-model

## Research summary
- **Project state**
  - The project uses the default `auth.User` (no `AUTH_USER_MODEL`). Django 6.1.1 on Python 3.14, with `DEFAULT_AUTO_FIELD` left at the default.
  - `apps.accounts` has `apps.py` (`AccountsConfig`, `name = 'apps.accounts'`, no `ready()`), `urls.py`, `views.py` and `tests/test_views.py`. It has no `models.py`, `admin.py` or `migrations/`; these are the project's first models.
  - `INSTALLED_APPS` lists `'apps.accounts'`. Because `apps.py` has a single `AppConfig` subclass, Django picks it up automatically, so a `ready()` hook will run.
  - `SignUpView` is a `CreateView` with the stock `UserCreationForm`. `form.save()` does a single `user.save()`, so `post_save` fires exactly once with `created=True`.
  - `createsuperuser` and `create_user` go through `save()` too. Nothing in `src/` uses `bulk_create` on users.
  - Nothing references `user.profile` yet. `base.html` only uses `user.is_authenticated` and `user.get_username`.
  - Admin is at `/admin/` with no customisation. The latest auth migration is `0012_alter_user_first_name_max_length`; the initial migration depends on `swappable_dependency(settings.AUTH_USER_MODEL)`.
  - The database is SQLite by default and Postgres via `DATABASE_URL`, so no Postgres-only field types.
- **Code style**
  - Double quotes, isort-ordered absolute imports, no docstrings, comments or type hints.
  - Ruff rules are `E,F,I,UP,B,DJ` with line length 100, and `**/migrations/*` is excluded.
  - DJ001: no `null=True` on CharFields. DJ008: every model needs `__str__`. DJ012: member order is fields, `Meta`, `__str__`, then other methods.
  - Ruff is not enforced by a hook, but `final-review` runs it.
- **Tests**
  - pytest-django; config in `pyproject.toml` (`pythonpath=["src"]`, `addopts="-q"`). There is no conftest, and no `--nomigrations`, so the test database is built by the real migrations.
  - Style: module-level functions with long behavioural names; arrange, blank line, assert; `@pytest.mark.django_db` per test; `parametrize` with `ids=`.
  - `test_views.py` has `PASSWORD`, a `user` fixture (`create_user(username="ada")`) and `signup_data()`. `admin_client` is not used yet.
  - `tests/test_smoke.py` already runs `call_command("check", fail_level="WARNING")`.
  - The suite is green at 36 passed. Single file: `.venv/bin/pytest src/apps/accounts/tests/test_models.py`.
  - A data-migration function can be tested directly: `importlib.import_module("apps.accounts.migrations.0002_backfill_profiles").backfill_profiles(django.apps.apps, None)`.

## Design decisions
- **Models live in `apps.accounts`** (`src/apps/accounts/models.py`). Profiles belong to the user/auth domain, and #4's profile page will sit next to sign-up.
- **`FocusArea`**: `name = CharField(max_length=50, unique=True)`, `Meta.ordering = ["name"]`, and `__str__` returns the name. Uniqueness is enforced by the database, as the ticket asks.
- **`Profile`**:
  - `user = OneToOneField(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="profile")`
  - `name = CharField(max_length=100, blank=True)` and `cohort = CharField(max_length=100, blank=True)`. Both are empty strings by default and never `null` (DJ001).
  - `focus_areas = ManyToManyField(FocusArea, blank=True, related_name="profiles")`
- **Auto-creation via a `post_save` receiver on `settings.AUTH_USER_MODEL`** in `src/apps/accounts/signals.py`. It is connected in `AccountsConfig.ready()` and creates the profile only when `created and not raw`. This covers sign-up, admin, `create_user` and `createsuperuser` without touching `SignUpView`, which stays unchanged (AC5).
  - The `raw` guard is defensive, not an AC. `loaddata` saves with `raw=True`, and a fixture that contains both a user and their profile would otherwise hit the one-to-one's unique constraint. The project has no fixture-loading requirements today (checked `instructions/`, the backlog, `src/` and `tests/`), so it gets one cheap regression test (step 4) and no AC.
  - Use a plain `create`, not `get_or_create`. When `created` is true no profile can exist yet, so the unique constraint exposes any double-creation bug instead of hiding it.
- **Backfill as a separate data migration** `0002_backfill_profiles.py`:
  - The module-level `backfill_profiles(apps, schema_editor)` uses `apps.get_model`, and creates one profile for every user where `profile__isnull=True`. Existing profiles are never touched, and re-running it is a no-op.
  - Reverse is `RunPython.noop`, so the migration can be unapplied without deleting user data.
- **One schema migration while the ticket is open.** `0001_initial` is created in step 1 and regenerated (deleted and re-run with `makemigrations accounts`) when a later step changes the schema. It doesn't stack 0001–0003 for one unreleased feature. Don't run `migrate` on the local dev database until step 3 is done; if you already did, run `migrate accounts zero` before regenerating. Tests always build a fresh database.
- **Admin**: `ProfileAdmin` (`list_display = ["user", "name", "cohort"]`) and `FocusAreaAdmin` (`list_display = ["name"]`, `search_fields = ["name"]`), registered with `@admin.register`. The default change form already exposes `name`, `cohort` and `focus_areas`. Nothing is added beyond that, such as `filter_horizontal` or a User inline.
- **Test files**:
  - `test_models.py`: models and the signal.
  - `test_views.py`: the existing file; gets the sign-up/profile test.
  - `test_migrations.py`: the backfill.
  - `test_admin.py`: admin pages, using the `admin_client` fixture.
- **Characterization steps** (6, 7, 8, 9, 10, 13): behaviour that already follows from earlier steps, such as CASCADE, the `created` check, the M2M field and the signal firing on sign-up. These tests may be green as soon as they're written. They are still required because they pin the AC. Each is checked by temporarily breaking the behaviour, watching the test go red, and reverting, as in #1 and #2. They are committed as `test(profile-model): ...`.
- **Red for step 11**: before writing the forward logic, scaffold `0002_backfill_profiles.py` with an empty `backfill_profiles` function. That way the test fails on an assertion, not on `ModuleNotFoundError`, as `.claude/rules/tdd.md` requires.

## Steps
- [x] 1. `str()` of a `FocusArea` is its name. Test: `src/apps/accounts/tests/test_models.py`. Impl: `src/apps/accounts/models.py` (`FocusArea` with `name` and `__str__`, no `unique` yet), `src/apps/accounts/migrations/__init__.py`, `migrations/0001_initial.py` (generated). Covers: AC3.
- [x] 2. Creating a second `FocusArea` with the same name raises `IntegrityError`. Test: `test_models.py`. Impl: `models.py` (`unique=True`, `Meta.ordering`), regenerate `0001_initial.py`. Covers: AC3.
- [x] 3. A user created with `create_user` has a `user.profile` with `name == ""`, `cohort == ""` and no focus areas, and `Profile.objects.filter(user=user).count() == 1`. Test: `test_models.py`. Impl: `models.py` (`Profile`, without `__str__`), regenerate `0001_initial.py`, `src/apps/accounts/signals.py` (`post_save` receiver, only when `created`; the `raw` guard is added in step 4), `apps.py` (`ready()` imports `signals`). Covers: AC1, AC2, AC6.
- [x] 4. *(defensive regression, no AC)* Sending `post_save` for a user that has no profile with `created=True, raw=True`, as `loaddata` does, creates no profile. Arrange: `create_user`, delete its auto-created profile, then `post_save.send(sender=User, instance=user, created=True, raw=True)`. Test: `test_models.py`. Impl: `signals.py` (`if created and not raw`). Covers: none. This is the defensive fixture-loading guard; see Design decisions.
- [x] 5. `str(user.profile)` is the user's username. Test: `test_models.py`. Impl: `models.py` (`Profile.__str__`). Covers: AC9.
- [x] 6. *(characterization)* A user created with `create_superuser` has exactly one profile. Test: `test_models.py`. Impl: none expected. Covers: AC6.
- [x] 7. *(characterization)* Changing and saving an existing user again (e.g. a new `first_name`, then `save()`) does not fail and leaves exactly one profile. Test: `test_models.py`. Impl: none expected. Covers: AC7.
- [x] 8. *(characterization)* Deleting a user deletes their profile. Test: `test_models.py`. Impl: none expected. Covers: AC1.
- [x] 9. *(characterization)* One profile can hold two focus areas, and one focus area can belong to two users' profiles; both directions are checked through the M2M. Test: `test_models.py`. Impl: none expected. Covers: AC4, AC2.
- [ ] 10. *(characterization)* A valid sign-up POST to `/accounts/signup/` creates exactly one profile for the new user, with empty `name` and `cohort` and no focus areas. The sign-up page has no `name`, `cohort` or `focus_areas` inputs. Test: `src/apps/accounts/tests/test_views.py`. Impl: none expected. Covers: AC5.
- [ ] 11. `backfill_profiles(apps, None)` creates exactly one profile for a user without one, leaves an existing profile unchanged (same pk, its `name` kept), and a second run creates nothing new. Arrange by deleting one user's auto-created profile and setting a `name` on another user's profile. Test: `src/apps/accounts/tests/test_migrations.py`. Impl: `migrations/0002_backfill_profiles.py` (scaffold an empty `backfill_profiles` first for an assertion-red, then fill it in; `RunPython(backfill_profiles, RunPython.noop)`). Covers: AC8.
- [ ] 12. For a superuser, the changelist and add pages of `Profile` and `FocusArea` (`/admin/accounts/profile/`, `/admin/accounts/profile/add/`, `/admin/accounts/focusarea/`, `/admin/accounts/focusarea/add/`) return 200. Parametrized with `ids=`. Test: `src/apps/accounts/tests/test_admin.py`. Impl: `src/apps/accounts/admin.py` (`ProfileAdmin`, `FocusAreaAdmin`). Covers: AC10.
- [ ] 13. *(characterization)* A superuser POSTs to a profile's admin change page with a new `name`, a new `cohort` and two focus areas. The response redirects, and the reloaded profile has those values. The change page has `name`, `cohort` and `focus_areas` inputs. Test: `test_admin.py`. Impl: none expected. Covers: AC10.

## Coverage
| AC | Steps |
|---|---|
| AC1 one-to-one, `user.profile`, cascade delete | 3, 8 |
| AC2 fields and defaults, M2M may be empty | 3, 9 |
| AC3 `FocusArea` unique name, `str` | 1, 2 |
| AC4 many focus areas per profile, shared across profiles | 9 |
| AC5 sign-up creates one empty profile, form unchanged | 10 |
| AC6 `create_user` / `create_superuser` create one profile | 3, 6 |
| AC7 re-saving a user creates no second profile | 7 |
| AC8 backfill migration | 11 |
| AC9 `str(profile)` is the username | 5 |
| AC10 admin registration and editing | 12, 13 |
| — defensive `raw` guard (no AC) | 4 |
