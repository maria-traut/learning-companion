# Review: goal-list-create
## Verdict: PASS
0 high, 0 medium findings. All 12 acceptance criteria are covered by passing tests. The full suite is green (117 passed), and `ruff check .` and `manage.py check` are clean.

## Acceptance criteria
All tests are in `src/apps/goals/tests/test_views.py`.
- AC1 — covered by `test_goal_list_redirects_anonymous_visitors_to_login` — PASS
- AC2 — covered by `test_goal_create_redirects_anonymous_visitors_to_login[get|post]` — PASS
- AC3 — covered by `test_goal_list_renders_for_logged_in_users` — PASS
- AC4 — covered by `test_goal_list_shows_title_status_and_created_date_newest_first` — PASS
- AC5 — covered by `test_goal_list_never_shows_another_users_goals` — PASS
- AC6 — covered by `test_goal_list_shows_empty_state_when_user_has_no_goals` — PASS
- AC7 — covered by `test_goal_list_links_to_goal_create_page` — PASS
- AC8 — covered by `test_goal_create_page_shows_title_description_and_status_fields` — PASS
- AC9 — covered by `test_valid_goal_create_saves_goal_for_user_and_redirects_with_message` — PASS
- AC10 — covered by `test_forged_owner_and_id_fields_cannot_touch_another_users_goal` (characterization) — PASS
- AC11 — covered by `test_invalid_goal_create_rerenders_form_with_error_and_saves_nothing[missing-title|missing-description|title-too-long|unknown-status]` (characterization) — PASS
- AC12 — covered by `test_nav_shows_goals_link_only_to_logged_in_users[logged-in|anonymous]` — PASS

## Findings
Code review (`code-reviewer`):
- [low] src/apps/goals/tests/test_views.py:163 — The anonymous POST payload for AC2 leaves out `status`, so the "no goal created" assertion would hold even without the login guard. The 302 assertion still catches that regression. — Add `"status": "planned"` so the no-goal check depends only on the login guard.
- [low] src/apps/goals/tests/test_views.py:108 — `goal.title` is put into the list-item regex unescaped. A future title with regex metacharacters would make the test match the wrong thing. — Use `re.escape(goal.title)`.
- [low] src/apps/goals/tests/test_views.py:268 — The missing-title and missing-description cases both look for "This field is required." anywhere on the page, so the test doesn't show the error is on the right field. — Optionally assert on `response.context["form"].errors` keys.
- [low] src/apps/goals/tests/test_views.py:76 — The anonymous list-redirect test has no `@pytest.mark.django_db`. It passes today, but would fail with a confusing database-access error if middleware ever queried the database for anonymous users. — Add the marker for consistency with the other tests in this file.

Security review (`security-reviewer`):
- [low] src/apps/goals/models.py:15 via src/apps/goals/forms.py:9 — `description` has no length limit. — Consider a `max_length` at the form or model boundary in a later ticket.
- [low] src/apps/goals/views.py:17 — Goal creation has no per-user quota or rate limit, so one user can create unlimited goals; it doesn't affect other users. — Accept the risk for now.
- Note (outside this diff): src/config/settings.py:31 — `SECRET_KEY` falls back to a hardcoded dev placeholder. — Fail at startup when `DEBUG` is False and the placeholder is in use. This is worth its own ticket.

Checked and fine:
- Both views use `LoginRequiredMixin`.
- The list is scoped by `request.user.goals`.
- The form only accepts `title`, `description` and `status`, and the owner is set on the server.
- Forms have CSRF tokens, templates rely on auto-escaping (no `|safe`), and `success_url` is fixed, so there's no open redirect.
- There are no secrets in the diff.

## Reviewed
commit 880d2af, 2026-10-02
