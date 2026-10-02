# Review: goal-model
## Verdict: PASS

- The suite is green (100 passed). `ruff check .`, `manage.py check` and `makemigrations --check` are clean.
- `goals` migrates forward and back on a scratch database.
- Neither reviewer found any high- or medium-severity issue.
- Every acceptance criterion is covered by a test that was shown to fail when the behaviour breaks.
- The code matches the plan's design decisions exactly. There is one commit per plan step, and characterization steps are committed as `test(...)`.

## Acceptance criteria
- **AC1**: covered by `test_goal_displays_as_its_title` and `test_user_goals_contains_exactly_that_users_goals`. All fields exist, and the step-4/6/8 tests use them. PASS
- **AC2**: covered by `test_goal_status_has_three_labelled_choices`, `test_new_goal_starts_as_planned_and_displays_status_label` and `test_full_clean_rejects_an_unknown_status`. PASS
- **AC3**: covered by `test_full_clean_requires_a_description` and `test_full_clean_requires_a_title_of_at_most_200_characters` (empty, 201 characters, 200 characters). PASS
- **AC4**: covered by `test_goal_timestamps_are_set_when_it_is_created` and `test_saving_a_goal_again_moves_only_updated_at`. PASS
- **AC5**: covered by `test_user_goals_contains_exactly_that_users_goals` and `test_deleting_a_user_deletes_only_their_goals`. PASS
- **AC6**: covered by `test_goals_are_listed_newest_first`. The expected order differs from both pk order and ascending order. PASS
- **AC7**: covered by `test_goal_displays_as_its_title`. PASS
- **AC8**: PASS. Covered by these tests:
  - `test_admin_goal_pages_load_for_a_superuser` (list and add)
  - `test_admin_goal_list_shows_title_owner_status_and_timestamps`
  - `test_admin_goal_list_can_be_filtered_by_status`, which pins `?status=done` as the requirement and also checks the filter link `?status__exact=done` as an extra
  - `test_admin_goal_list_can_be_searched_by_title`
- **AC9**: PASS. Covered by these tests:
  - `test_superuser_can_add_a_goal_for_a_chosen_owner`
  - `test_crafted_post_cannot_change_a_goals_owner`. This test checks both that the owner field isn't rendered and that the stored owner doesn't change. The stored-owner assertion was confirmed on its own with a break that kept the field hidden but applied the POSTed owner.
  - `test_goal_timestamps_are_shown_read_only_in_the_admin`

## Findings
The code review (`code-reviewer`) found 0 high, 0 medium and 3 low. The security review (`security-reviewer`) also found 0 high, 0 medium and 3 low. The security review found these areas clean:
- admin access and ownership reassignment, which is read-only on change and enforced on the server
- mass assignment of the timestamps
- XSS (autoescaped admin)
- injection (ORM only)
- cascade deletes (intended)
- secrets

All six lows are left as follow-ups and do not block release.

**Test hardening (code review):**
- [low] `src/apps/goals/tests/test_admin.py:100,126-127`: the change- and add-page GETs are decoded without checking `status_code`. Their negative `name="..."` assertions would also pass on an error page. Recommendation: assert 200 before the negative checks.
- [low] `src/apps/goals/tests/test_admin.py:131`: the read-only timestamp regex isn't anchored to its own field container, though the negative `name="{field}"` check backs it up. Recommendation: limit the match to the field's own block.
- [low] `src/apps/goals/tests/test_models.py:56-61`: the `planned` default is checked on the in-memory instance. Recommendation: `refresh_from_db()` first, to confirm the stored value.

**Hardening for the user-facing goal tickets #6/#7 (security review):**
- [low] `src/apps/goals/models.py:16`: status choices are enforced only through validation (`full_clean()` and forms), not by the database. Recommendation: add a `CheckConstraint` (`status__in=Goal.Status.values`) with its own migration once code paths that skip validation exist.
- [low] `src/apps/goals/models.py:15`: `description` is unbounded, which becomes a cost and abuse risk once user-written text is sent to OpenAI (#15/#16). Recommendation: cap the length at the form or model boundary when #6/#7 add user-facing forms, with a test.
- [low] `src/apps/goals/models.py:11-13`: there is no owner-scoped query helper. Recommendation: a `Goal.objects.for_user(user)` queryset method for #6/#7, used with `get_object_or_404`, plus the 404 test for another user's goal that CLAUDE.md requires.

**Outside this diff**, also noted in #4: the `SECRET_KEY` fallback in `src/config/settings.py:31`. A separate chore should require it when `DEBUG` is off.

## Reviewed
commit 465b690, 2026-10-02
