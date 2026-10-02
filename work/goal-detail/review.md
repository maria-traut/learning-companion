# Review: goal-detail
## Verdict: PASS
0 high, 0 medium findings. All 13 acceptance criteria are covered by passing tests. The full suite is green (145 passed), and `ruff check .` and `manage.py check` are clean. `makemigrations --check` confirms `Goal.get_absolute_url` needs no migration.

## Acceptance criteria
All tests are in `src/apps/goals/tests/test_views.py`.
- AC1 — covered by `test_goal_detail_redirects_anonymous_visitors_to_login`, `test_goal_edit_redirects_anonymous_visitors_to_login[get|post]`, `test_goal_delete_redirects_anonymous_visitors_to_login[get|post]` — PASS
- AC2 — covered by `test_goal_detail_renders_for_its_owner` — PASS
- AC3 — covered by `test_goal_detail_shows_all_goal_fields` — PASS
- AC4 — covered by `test_goal_detail_links_to_edit_and_delete` — PASS
- AC5 — covered by `test_goal_list_titles_link_to_their_detail_pages` — PASS
- AC6 — covered by `test_goal_edit_page_shows_form_prefilled_with_the_goal` — PASS
- AC7 — covered by `test_valid_goal_edit_saves_changes_and_redirects_to_detail_with_message` — PASS
- AC8 — covered by `test_forged_owner_and_id_fields_in_edit_cannot_touch_another_users_goal` (characterization) — PASS
- AC9 — covered by `test_invalid_goal_edit_rerenders_form_with_error_and_leaves_goal_unchanged[missing-title|missing-description|title-too-long|unknown-status]` (characterization) — PASS
- AC10 — covered by `test_goal_delete_page_asks_to_confirm_deleting_the_goal` — PASS
- AC11 — covered by `test_goal_delete_removes_the_goal_and_redirects_to_list_with_message` — PASS
- AC12 — covered by `test_goal_detail_returns_404_for_another_users_or_missing_goal[other-user]`, `test_goal_edit_returns_404_for_another_users_or_missing_goal[other-user-get|other-user-post]`, `test_goal_delete_returns_404_for_another_users_or_missing_goal[other-user-get|other-user-post]` — PASS
- AC13 — covered by the same three tests' `missing` cases (detail GET, edit GET/POST, delete GET/POST) — PASS

## Findings
Code review (`code-reviewer`):
- [low] src/apps/goals/views.py:33 — `GoalUpdateView` relies on `UpdateView`'s default template (`goals/goal_form.html`), while `GoalCreateView` sets `template_name` explicitly. The plan's step 7 mentioned setting `template_name`. Both views render the same template either way. — For consistency, set `template_name` explicitly or keep the default on purpose.
- [low] src/apps/goals/tests/test_views.py:395 — In the edit 404 test's `missing` case, `assert not Goal.objects.filter(title=EDITED["title"]).exists()` can't fail, because no goals exist. — Assert it only for `other-user`, or seed a goal for Ada.
- [low] src/apps/goals/tests/test_views.py:445-446 (also 249/253 for create) — The missing-title and missing-description cases both look for "This field is required." anywhere on the page, so the test doesn't show the error is on the right field. The database-unchanged assertion catches the realistic regression. — Optionally assert on `response.context["form"].errors[field]`.
- [low] src/apps/goals/tests/test_views.py:182-191, 366-379 — Nothing tests the conditional heading/title in the shared `goal_form.html` beyond the edit `<h1>`: not the edit `<title>`, and not that create still says "New goal". — Assert the create page's `<h1>`/`<title>` and the edit page's `<title>`.
- [low] src/apps/goals/tests/test_views.py:327 — The AC3 check `"Learn Django" in main` doesn't say where the title appears. — Match the `<h1>` instead.

Security review (`security-reviewer`):
- [low] src/apps/goals/tests/test_views.py:347-528 — No test proves CSRF is enforced on edit and delete, because the Django test client skips CSRF checks. CSRF protection is active today: `CsrfViewMiddleware` is on, both forms include `{% csrf_token %}`, and there's no `csrf_exempt`. — Add a `Client(enforce_csrf_checks=True)` test that a POST without a token returns 403 and changes nothing.
- [low] src/config/settings.py:31 (unchanged in this diff, same note as goal-list-create) — `SECRET_KEY` falls back to a hardcoded dev placeholder. — Fail at startup without a real key when `DEBUG` is off. This needs its own ticket.

Checked and fine:
- **Ownership:** a single `OwnGoalMixin` (`LoginRequiredMixin` + `request.user.goals.all()`) scopes list, detail, edit and delete. Another user's goal and a missing pk both return 404 on GET and POST, and anonymous visitors are redirected before any lookup.
- **Mass assignment:** `GoalForm` only accepts `title`, `description` and `status`.
- **Delete safety:** a GET to the delete URL only shows the confirmation page; deletion requires a POST with a CSRF token.
- **XSS:** templates rely on auto-escaping, and `linebreaksbr` escapes its input.
- **Redirects:** the targets are fixed (`goals:list`, `get_absolute_url`), so there's no open redirect.

## Reviewed
commit f5e5531, 2026-10-02
