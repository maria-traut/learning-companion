# Review: profile-model
## Verdict: FAIL

The suite is green (53 passed), ruff is clean, `manage.py check` and `makemigrations --check` are clean, and there are no high-severity findings. The verdict is FAIL because AC2 is only partly covered. No test pins that `name`, `cohort` and `focus_areas` are *optional*, i.e. that a profile with all three empty can be saved through a form. Removing `blank=True` from any of them would leave the suite green.

## Acceptance criteria
- AC1: covered by `test_create_user_gives_the_user_one_empty_profile` and `test_deleting_a_user_deletes_their_profile`. PASS. The cascade test can pass vacuously; see the low finding below.
- AC2: covered by `test_create_user_gives_the_user_one_empty_profile` and `test_profiles_and_focus_areas_are_many_to_many`. **PARTIAL.** The empty defaults and the M2M are pinned, but optionality (`blank=True`) is not.
- AC3: covered by `test_focus_area_displays_as_its_name` and `test_focus_area_names_are_unique`. PASS
- AC4: covered by `test_profiles_and_focus_areas_are_many_to_many`. PASS
- AC5: covered by `test_valid_signup_creates_one_empty_profile_for_the_new_user` and `test_signup_page_asks_for_no_profile_fields`. PASS. "Form unchanged" is only checked negatively; see the low finding below.
- AC6: covered by `test_create_user_gives_the_user_one_empty_profile` and `test_create_superuser_gives_the_user_one_profile`. PASS
- AC7: covered by `test_saving_an_existing_user_again_keeps_one_profile`. PASS
- AC8: covered by `test_backfill_creates_missing_profiles_and_leaves_existing_ones_unchanged`. PASS. It doesn't check that the function is wired into `RunPython`; see the low finding below.
- AC9: covered by `test_profile_displays_as_its_users_username`. PASS
- AC10: covered by `test_admin_pages_for_profiles_and_focus_areas_load_for_a_superuser` (4 cases) and `test_superuser_can_edit_name_cohort_and_focus_areas_of_a_profile`. PASS
- Defensive `raw` guard (no AC): covered by `test_raw_save_as_in_loaddata_creates_no_profile`. PASS

## Findings
Code review (`code-reviewer`) found 0 high, 1 medium and 8 low. Security review (`security-reviewer`) found 0 high, 0 medium and 2 low. The security review checked:
- no exposure of profiles to non-staff users
- no mass-assignment surface
- no raw SQL or `mark_safe`
- no secrets
- correct cascade behaviour and a backfill that is safe to re-run

Turned into plan steps (14–20):
- [medium] `src/apps/accounts/models.py:19-21`: optionality of `name`, `cohort` and `focus_areas` (`blank=True`) is untested, so AC2 is only partly covered. Recommendation: have a superuser save a profile with all three empty through the admin and assert it succeeds. Plan step 14.
- [low] `src/apps/accounts/tests/test_models.py:56`: the cascade test asserts `not Profile.objects.exists()` without first checking that a profile existed, so it can pass vacuously. Recommendation: capture the profile's pk before deleting and assert that pk is gone. Plan step 15.
- [low] `src/apps/accounts/tests/test_migrations.py:22`: the test calls `backfill_profiles` directly but never checks that `0002` runs it, so `RunPython(noop, ...)` would go unnoticed. Recommendation: assert that the migration's `RunPython` code is `backfill_profiles`. Plan step 16.
- [low] `src/apps/accounts/tests/test_views.py:96`: "sign-up form unchanged" is only checked negatively, so an added `full_name` field would pass. Recommendation: assert the exact set of form inputs. Plan step 17.
- [low] `src/apps/accounts/tests/test_models.py:65` and `test_admin.py:32`: a local variable named `django` shadows the package. Recommendation: rename it to `django_area` / `sql_area`. Plan step 18.
- [low] (security) `src/apps/accounts/admin.py:7`: on an existing profile, the `user` field is editable, so staff can re-link one person's profile to another account. Recommendation: make `user` read-only when editing, and keep it editable on the add page. Plan step 19.
- [low] `work/auth/activity.log`: the branch carries an unrelated `WRITE README.md` line from the docs hotfix into the previous ticket's log. Recommendation: remove that line on this branch. Plan step 20.

Recorded and deliberately not turned into steps:
- [low] (code and security) `src/apps/accounts/signals.py:11`: creating the user and the profile is not atomic without `ATOMIC_REQUESTS`, and `get_or_create` was suggested. Kept as is. Plain `create` is a plan decision: on `created=True` no profile can exist yet, so the unique constraint should surface double creation. The admin add view is already atomic. Later tickets that read `request.user.profile` (#4) should not assume more than this; making sign-up atomic belongs in a later ticket if it is wanted.
- [low] `src/apps/accounts/signals.py:11`: the `using` kwarg is ignored. The project has a single database, so this is not applicable.
- [low] `src/apps/accounts/admin.py:8`: there is no `list_select_related = ["user"]`, so the Profile list runs one extra query per row. This is a performance issue at a scale that doesn't apply here; it is a candidate for a later admin ticket.
- [low] `PASSWORD` and the `user` fixture are duplicated across the accounts test files. Moving them to `src/apps/accounts/tests/conftest.py` is a follow-up refactor outside this ticket, as the reviewer suggested.

## Reviewed
commit 43f8a1c, 2026-10-02
