# Plan: learning-session-model

## Research summary
- **Precedent models.**
  - `goals.Goal` has a `user` FK (`related_name="goals"`), `Status` as nested `TextChoices`, `Meta.ordering = ["-created_at"]`, and `__str__` returning the title.
  - Tags follow `accounts.FocusArea`: `name = CharField(max_length=50, unique=True)`, `ordering = ["name"]`, `__str__` returning the name, used through an M2M field.
  - Neither AppConfig sets `default_auto_field`, and settings has no `DEFAULT_AUTO_FIELD`. Migrations use `BigAutoField`.
  - Settings: `TIME_ZONE = "UTC"`, `USE_TZ = True`.
- **New app.** Created with `startapp` into `src/apps/learning_sessions`, with `name = "apps.learning_sessions"`, and appended to `INSTALLED_APPS` after `'apps.goals'` (`src/config/settings.py:41`).
- **Test conventions.**
  - Plain pytest functions in `src/apps/<app>/tests/test_*.py`, each folder with an `__init__.py`. There is no conftest and no factories.
  - Each file defines a `user` fixture with `PASSWORD = "correct-horse-battery-9"`; "ada" is the main user and "grace" the second one.
  - Objects are created with `objects.create`. DB tests use `@pytest.mark.django_db`. `__str__` tests use unsaved instances and no DB.
  - Validation: plain `full_clean()` inside `pytest.raises(ValidationError)`, asserting `set(excinfo.value.error_dict)` and the error codes. Boundaries are covered with parametrized `(value, valid)` cases.
  - Ordering: rows are created first, then timestamps are set with `QuerySet.update()`. There is no freezegun and no monkeypatch.
  - Cascade: delete one owner's object, then assert `exists()` on both owners' rows.
- **Admin tests** go through `admin_client` HTTP requests:
  - List columns: a regex on `<th scope="col" ... class="column-<field>">`.
  - Filters: a regex on the `<search id="changelist-filter">` sidebar, plus `context["cl"].result_list` for a filtered query.
  - Search: `?q=` and `set(context["cl"].result_list)`.
  - The add view is tested with a POST that expects a 302.
- **Migrations.** Earlier tickets ran `makemigrations --check` by hand at the end. This ticket adds a test for it, because AC1 must be checked by a test.
- **Running tests.** `.venv/bin/pytest src/apps/learning_sessions/tests/test_models.py`, or the full suite with `.venv/bin/pytest`.

## Design decisions
- **Own app `apps.learning_sessions`, holding both `Tag` and `LearningSession`.** The name `sessions` would clash with `django.contrib.sessions`.
- **`date = DateField(default=timezone.localdate, validators=[validate_not_in_future])`.**
  - Both the default and the future check use `timezone.localdate()`, so "today" means the same thing in both places.
  - A field validator puts the error under the `date` key, which matches how the tests assert errors.
  - Tests build future and past dates relative to `localdate()`, so no time freezing is needed.
- **`duration_minutes = PositiveIntegerField(validators=[MinValueValidator(1)])`.** `PositiveIntegerField` on its own accepts 0.
- **`notes = TextField(blank=True)`.**
- **`goal = ForeignKey(Goal, on_delete=CASCADE, related_name="sessions")`.** The owner is reached through `goal.user`; there is no separate `user` field.
- **`tags = ManyToManyField(Tag, related_name="sessions")` without `blank=True`.**
  - Every ModelForm (the admin now, the #10 forms later) then requires at least one tag (AC8).
  - `full_clean` does not check M2M fields, so this check lives only in forms.
- **`created_at = DateTimeField(auto_now_add=True)` and `Meta.ordering = ["-date", "-created_at"]`.**
  - The ticket doesn't list `created_at`, but AC9 needs it to order sessions on the same date.
- **`__str__` returns `f"{goal.title} – {date:%Y-%m-%d} ({duration_minutes} min)"`.** The dash is an en dash, as in AC10.
- **Admin, `LearningSessionAdmin`:**
  - `list_display = ["goal", "date", "duration_minutes"]`
  - `list_filter = ["date", "tags"]`
  - `search_fields = ["notes", "goal__title"]`
  - `filter_horizontal = ["tags"]` is optional and only for usability.
- **Admin, `TagAdmin`:** `list_display = ["name"]`, `search_fields = ["name"]`.
- **One schema migration while the ticket is open, following #5 (goal-model).** `0001_initial` is regenerated (delete it, then run `makemigrations learning_sessions`) whenever a step changes the schema. Read "migration 0002" and "+ migration" in the steps below in that sense.
- **First-model scaffolding, following #5.** A bare model is scaffolded before the first test of each new model (`Tag` in step 2, `LearningSession` in step 5). The test then fails on its assertion instead of on an import error. `LearningSession` starts with only `goal`, `date` and `duration_minutes`. Each other field is added in the step that tests it: `notes` in step 8, `tags` in step 11, `created_at` in step 12.
- **Three guard tests may pass on their first run:**
  - Step 13 (deleting) passes because `CASCADE` and M2M cleanup already exist.
  - Step 14 (no pending migrations) passes as soon as the migrations are kept up to date.
  - Step 19 (admin requires a tag) passes because the model leaves out `blank=True`.
  - `tdd-implement` records each as a guard test that passed on first run. It must not change working code just to make these tests fail first.

## Steps
- [x] 1. The app `apps.learning_sessions` is installed (`django.apps.apps.is_installed`). Test: `src/apps/learning_sessions/tests/test_apps.py`. Impl: `startapp`, `apps.py` (`name`), `INSTALLED_APPS` in `src/config/settings.py`, and a `tests/__init__.py`. Covers AC1.
- [x] 2. A `Tag` displays as its name (unsaved instance, no DB). Test: `tests/test_models.py`. Impl: `models.py` (`Tag.name`, `__str__`), plus migration `0001_initial`. Covers AC2.
- [x] 3. `Tag.full_clean` rejects an empty name, a name over 50 characters, and a duplicate name; it accepts 50 characters. Test: `tests/test_models.py` (parametrized, plus a duplicate case). Impl: `max_length=50`, `unique=True`, and a migration if needed. Covers AC2.
- [x] 4. Tags list in name order. Test: `tests/test_models.py`. Impl: `Tag.Meta.ordering`, plus a migration. Covers AC2.
- [x] 5. A session displays as `"<goal title> – <YYYY-MM-DD> (<n> min)"`, using an unsaved instance with an unsaved goal. Test: `tests/test_models.py`. Impl: the `LearningSession` model (`goal`, `date`, `duration_minutes`, `notes`, `tags`, `created_at`), `__str__`, and migration `0002`. Covers AC3 and AC10.
- [x] 6. `goal.sessions` returns that goal's sessions. Test: `tests/test_models.py`. Impl: `related_name="sessions"`, if step 5 didn't already set it. Covers AC3.
- [x] 7. `full_clean` rejects `duration_minutes` of 0 and -5 with error key `duration_minutes`, and accepts 1. Test: `tests/test_models.py` (parametrized). Impl: `MinValueValidator(1)`, plus a migration. Covers AC5.
- [x] 8. `full_clean` reports errors for both `goal` and `date` when they are missing, and accepts `notes=""`. Test: `tests/test_models.py`. Impl: `notes` gets `blank=True`, plus a migration. Covers AC6 and AC3.
- [x] 9. A session created without a `date` gets `timezone.localdate()`. Test: `tests/test_models.py`. Impl: `default=timezone.localdate`, plus a migration. Covers AC4.
- [x] 10. `full_clean` rejects `localdate() + 1 day` with error key `date`, and accepts today and `localdate() - 30 days`. Test: `tests/test_models.py` (parametrized). Impl: `validate_not_in_future` in `models.py` (or `validators.py`) attached to `date`, plus a migration. Covers AC7.
- [x] 11. A session can carry several tags, and a tag can be on several sessions, reachable through `tag.sessions`. Test: `tests/test_models.py`. Impl: `related_name="sessions"` on `tags`, if step 5 didn't already set it. Covers AC12 and AC3.
- [x] 12. Sessions list newest `date` first; sessions on the same date list newest `created_at` first. Timestamps are set with `QuerySet.update()`. Test: `tests/test_models.py`. Impl: `Meta.ordering = ["-date", "-created_at"]`, plus a migration. Covers AC9.
- [ ] 13. Deletion, in three cases:
  - Deleting a goal deletes its sessions.
  - Deleting a tag removes it from the session's tags but keeps the session.
  - Deleting a user deletes only their goals' sessions.
  Test: `tests/test_models.py` (one test per case, kept in one step). Impl: `on_delete=CASCADE`, which should already be in place, so this is a guard test. Covers AC11.
- [ ] 14. No migrations are pending for `learning_sessions`: `call_command("makemigrations", "learning_sessions", "--check", "--dry-run")` does not raise `SystemExit`. Test: `tests/test_migrations.py`. Impl: none if the migrations are current, so this is a guard test. Covers AC1.
- [ ] 15. The session admin list page returns 200 and shows the `goal`, `date` and `duration_minutes` columns. Test: `tests/test_admin.py`. Impl: `admin.py` (`LearningSessionAdmin`, `list_display`). Covers AC13.
- [ ] 16. The session admin sidebar has "By date" and "By tags" filters, and `?tags__id__exact=<id>` lists only sessions with that tag. Test: `tests/test_admin.py`. Impl: `list_filter`. Covers AC13.
- [ ] 17. Searching the session admin with `?q=` matches sessions by notes and by goal title. Test: `tests/test_admin.py`. Impl: `search_fields`. Covers AC13.
- [ ] 18. The Tag admin is registered: its list page returns 200, and `?q=` filters tags by name. Test: `tests/test_admin.py`. Impl: `TagAdmin`. Covers AC13 and AC2.
- [ ] 19. The session admin add page:
  - A POST with no tags re-renders with a `tags` error and creates no session.
  - The same POST with one tag returns 302 and creates the session.
  Test: `tests/test_admin.py`. Impl: none expected, because the model has no `blank=True` on `tags`, so this is a guard test. Covers AC8.
- [ ] 20. Wrap-up, with no new test: run `.venv/bin/ruff check .`, `.venv/bin/python src/manage.py check`, and the full `.venv/bin/pytest`. Update the `CLAUDE.md` architecture list if it needs it.

(All test paths are under `src/apps/learning_sessions/`.)

## Coverage
| AC | Steps |
|----|-------|
| AC1 app installed, migrations clean | 1, 14 |
| AC2 Tag name, unique, ordering, str | 2, 3, 4, 18 |
| AC3 LearningSession fields | 5, 6, 8, 11 |
| AC4 date defaults to today | 9 |
| AC5 duration ≥ 1 | 7 |
| AC6 goal/date required, notes optional | 8 |
| AC7 no future dates | 10 |
| AC8 at least one tag (admin form) | 19 |
| AC9 ordering | 12 |
| AC10 display string | 5 |
| AC11 delete behaviour | 13 |
| AC12 sessions ↔ tags M2M | 11 |
| AC13 admin | 15, 16, 17, 18 |
