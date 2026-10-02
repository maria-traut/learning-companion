# Plan: goal-model

## Research summary
- **New app**
  - `startapp` creates `__init__.py`, `migrations/__init__.py` and stub `admin.py`, `apps.py`, `models.py`, `tests.py` and `views.py`. Earlier apps never committed unused stubs, so each file arrives with the step that needs it. Every app uses a `tests/` package instead of `tests.py`.
  - `apps.py` keeps startapp's single quotes, with `name = 'apps.goals'`.
  - `INSTALLED_APPS` in `src/config/settings.py` uses single quotes. `'apps.goals'` goes after `'apps.accounts'`.
  - `src/apps/goals/tests/__init__.py` is required. Without it, `goals/tests/test_models.py` would clash with `accounts/tests/test_models.py` under pytest's default `prepend` import mode.
  - `DEFAULT_AUTO_FIELD` is unset, which means `BigAutoField` in Django 6.1. The smoke test runs `check` with `fail_level="WARNING"`, and a bare `GoalsConfig` raises no warning.
- **Model behaviour (Django 6.1.1 source)**
  - `class Status(models.TextChoices)`, with members like `PLANNED = "planned", "Planned"`, can be passed directly as `choices=Status`.
  - `full_clean()`:
    - reports an invalid choice with code `invalid_choice`
    - rejects an empty `CharField`/`TextField` that has no `blank=True`, and a too-long `CharField` (`max_length`)
    - never complains about `auto_now`/`auto_now_add` fields, which are non-editable and blank
  - `auto_now_add` is set only on insert, and `auto_now` on every `save()`. `QuerySet.update()` bypasses both, so tests use it to set known timestamps and avoid ties. `freezegun` is not installed.
- **Admin behaviour (Django 6.1.1 source)**
  - **Status filter:** `list_filter = ["status"]` generates `?status__exact=<value>` links and a filter sidebar (`#changelist-filter`, "By status"). A plain `?status=done` also filters, through the remaining lookup params, even without `list_filter`. So the sidebar is what pins `list_filter`.
  - **Search:** `search_fields` works through `?q=`. Without `search_fields`, `q` is ignored and every row is shown.
  - **Results in tests:** `response.context["cl"].result_list` is the most robust way to check the result set. Column headers render as `<th scope="col" class="... column-<field>">`.
  - **Timestamps on the form:** non-editable timestamps only appear when they are listed in readonly fields. They then render as `<div class="readonly">` inside `div.field-created_at` / `div.field-updated_at`, with no input. The default `get_fields` appends readonly fields, so no `fields`/`fieldsets` setting is needed.
  - **Read-only owner:** listing `user` in readonly fields excludes it from the form, so a POSTed `user` is ignored on the change page. This is the Profile pattern.
  - **Redirects:** an add or change POST without `_continue`/`_addanother` redirects to the changelist.
- **Tests**
  - Plain pytest functions with `@pytest.mark.django_db`, the `PASSWORD` constant and a `user` fixture per module. There's no `conftest.py`.
  - `admin_client` and hard-coded admin URLs. Regex checks on page HTML, and `refresh_from_db()` after a POST.
  - The suite has 79 passing tests. No CI runs the tests or `makemigrations --check`, so `tdd-implement` runs `makemigrations --check` at the end.

## Design decisions
- **New app `apps.goals`** at `src/apps/goals/`. The model lives in `models.py`, admin in `admin.py`, and tests in `tests/test_models.py` and `tests/test_admin.py`.
- **`Goal` fields:**
  - `user = ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="goals")`
  - `title = CharField(max_length=200)`
  - `description = TextField()`, required with no `blank`
  - `status = CharField(max_length=20, choices=Status, default=Status.PLANNED)`
  - `created_at = DateTimeField(auto_now_add=True)` and `updated_at = DateTimeField(auto_now=True)`
  - `Meta.ordering = ["-created_at"]`, and `__str__` returns `title`
  - No `null` on text fields (DJ001). Member order follows DJ012: `Status`, then fields, `Meta`, `__str__`.
- **`Goal.Status` is nested in the model** (`Goal.Status.IN_PROGRESS`), so #8 and #17 can import the choices together with the model.
- **One schema migration while the ticket is open.** `0001_initial` is regenerated (delete it, run `makemigrations goals`) whenever a step changes the schema, as in #3. Don't migrate the local dev DB until the last schema step (step 9) is done.
- **`GoalAdmin`:**
  - `list_display = ["title", "user", "status", "created_at", "updated_at"]`
  - `list_filter = ["status"]`
  - `search_fields = ["title"]`
  - `get_readonly_fields` returns `["created_at", "updated_at"]` on add and `["user", "created_at", "updated_at"]` on change
- **The "required" ACs are tested through `full_clean()`** (AC3) and the admin form, because the database accepts empty strings.
- **AC8's `?status=done`.** The user-facing requirement is the `?status=done` behaviour, and it's what the test pins. Django's own filter-link format (`?status__exact=done`) is checked only as an extra assertion and is not part of the requirement.
- **Characterization steps (3, 5, 7, 14).** Their behaviour follows from earlier steps: CASCADE, `choices`, `max_length` and non-blank title, and the default admin add form. Their tests may pass as soon as they're written. Each is checked by temporarily breaking the behaviour, seeing it go red, and reverting, committed as `test(goal-model): ...`. Temporary breaks use the Edit tool or `/bin/cp -f` on a scratch copy, never the aliased `cp`/`rm`.
- **Red reasons that aren't plain assertions:**
  - **Step 1:** the new app and model don't exist yet, so the first test would fail with an import error. As in #3, the bare `Goal` model with only `title` is scaffolded first, so the test fails on its `__str__` assertion.
  - **Step 8:** the timestamp test fails with `AttributeError` (no `created_at` yet). That is the missing behaviour itself, named here so it can be confirmed.

## Steps
- [x] 1. `str(Goal(title="Learn Django"))` is `"Learn Django"`. Test: `src/apps/goals/tests/test_models.py` (plus `tests/__init__.py`). Impl:
  - `startapp goals` into `src/apps/goals/`; keep only `__init__.py`, `apps.py` (`name = 'apps.goals'`) and `migrations/__init__.py`
  - add `'apps.goals'` to `INSTALLED_APPS`
  - `models.py` (`Goal` with `title`, scaffolded without `__str__` for the red, then `__str__`)
  - `migrations/0001_initial.py` (generated)

  Covers: AC7, AC1.
- [x] 2. A user can own several goals. `user.goals` contains exactly that user's goals and none of another user's. Test: `test_models.py`. Impl: `models.py` (`user` FK, `related_name="goals"`, CASCADE), regenerate `0001_initial.py`. Covers: AC1, AC5.
- [x] 3. *(characterization)* Deleting a user deletes their goals and leaves another user's goal in place. Test: `test_models.py`. Impl: none expected. Verify with a temporary `on_delete=DO_NOTHING`. Covers: AC5.
- [x] 4. A new goal's `status` is `"planned"`. `Goal.Status` has exactly the values `planned`, `in_progress` and `done`, labelled "Planned", "In progress" and "Done", and `get_status_display()` returns the label. Test: `test_models.py`. Impl: `models.py` (`Status` TextChoices, `status` field), regenerate `0001_initial.py`. Covers: AC2.
- [ ] 5. *(characterization)* `full_clean()` on a goal whose status is `"archived"` raises a `ValidationError` with an `invalid_choice` error on `status`. Test: `test_models.py`. Impl: none expected. Verify by temporarily removing `choices=`. Covers: AC2.
- [ ] 6. `full_clean()` on a goal with `description = ""` raises a `ValidationError` on `description`, and a goal with a non-empty description passes `full_clean()`. Test: `test_models.py`. Impl: `models.py` (`description = TextField()`), regenerate `0001_initial.py`. Expected red: "DID NOT RAISE", since an unknown attribute isn't validated. Covers: AC3.
- [ ] 7. *(characterization)* `full_clean()` raises a `ValidationError` on `title` for an empty title and for a 201-character title, but accepts a 200-character title. Parametrized with `ids=`. Test: `test_models.py`. Impl: none expected. Verify by temporarily setting `blank=True, max_length=255`. Covers: AC3.
- [ ] 8. A newly created goal has `created_at` and `updated_at` within the window from just before to just after `create()`. After `updated_at` and `created_at` are set to a fixed past time via `QuerySet.update()`, changing the title and calling `save()` leaves `created_at` at the fixed time and moves `updated_at` past it. Test: `test_models.py`. Impl: `models.py` (`created_at` with `auto_now_add`, `updated_at` with `auto_now`), regenerate `0001_initial.py`. Expected red: `AttributeError`. Covers: AC4.
- [ ] 9. `Goal.objects.all()` lists goals newest first by `created_at`. Three goals get distinct `created_at` values via `QuerySet.update()`, set out of creation order. Test: `test_models.py`. Impl: `models.py` (`Meta.ordering = ["-created_at"]`), regenerate `0001_initial.py`. Covers: AC6.
- [ ] 10. For a superuser, `/admin/goals/goal/` and `/admin/goals/goal/add/` return 200. Parametrized with `ids=`. Test: `src/apps/goals/tests/test_admin.py`. Impl: `src/apps/goals/admin.py` (`@admin.register(Goal) class GoalAdmin`). Covers: AC8.
- [ ] 11. The goal changelist has column headers for `title`, `user`, `status`, `created_at` and `updated_at`, matched as `column-<field>`. Test: `test_admin.py`. Impl: `GoalAdmin.list_display`. Covers: AC8.
- [ ] 12. The changelist shows a "By status" filter with Planned, In progress and Done. The requirement is that `?status=done` lists only the done goals (`response.context["cl"].result_list`). As an extra, non-normative check, the filter's own `Done` link (`?status__exact=done`) gives the same result. Test: `test_admin.py`. Impl: `GoalAdmin.list_filter`. Covers: AC8.
- [ ] 13. `?q=django` lists only the goals whose title contains "django" (case-insensitive). Test: `test_admin.py`. Impl: `GoalAdmin.search_fields`. Covers: AC8.
- [ ] 14. *(characterization)* The add page has a `<select name="user">`. Posting `user`, `title`, `description` and `status` redirects to `/admin/goals/goal/` and creates exactly one goal with that owner and those values. Test: `test_admin.py`. Impl: none expected. Verify with a temporary `exclude = ["user"]` on `GoalAdmin`. Covers: AC9.
- [ ] 15. On a goal's change page:
  - there is no `name="user"` input
  - a crafted POST with `user=<grace.pk>` plus a new title, description and status redirects. Reloaded from the database (`Goal.objects.get(pk=...)`), the goal's owner is still ada, and the new title, description and status are saved. Both halves are tested: the field isn't rendered, and the stored owner doesn't change
  - there are no `created_at`/`updated_at` inputs; both are shown as `div.readonly` inside `field-created_at` / `field-updated_at`

  The add page still has no timestamp inputs. Test: `test_admin.py`. Impl: `GoalAdmin.get_readonly_fields` (timestamps always, `user` only when `obj` is set). Covers: AC9.

## Coverage
| AC | Steps |
|---|---|
| AC1 `goals` app, `Goal` fields, `user.goals` | 1, 2 (fields completed by 4, 6, 8) |
| AC2 status choices, labels, default, invalid rejected | 4, 5 |
| AC3 title and description required, title ≤ 200 | 6, 7 |
| AC4 timestamps set automatically; resave moves only `updated_at` | 8 |
| AC5 several goals per user, only own in `user.goals`, cascade | 2, 3 |
| AC6 newest first | 9 |
| AC7 `str(goal)` is the title | 1 |
| AC8 admin list/add load; columns; status filter; title search | 10, 11, 12, 13 |
| AC9 add with chosen owner; change: owner read-only, fields editable, timestamps read-only | 14, 15 |
