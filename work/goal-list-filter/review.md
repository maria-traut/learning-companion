# Review: goal-list-filter

## Verdict: PASS

## Acceptance criteria
All tests below are in `src/apps/goals/tests/test_views.py`.

- AC1 — covered by `test_goal_list_filtered_by_status_shows_only_own_matching_goals_newest_first[planned|in_progress|done]` — PASS
- AC2 — covered by the same test as AC1 (another user's goal in the requested status is never shown) — PASS
- AC3 — covered by `test_goal_list_ignores_missing_empty_or_unknown_status[no-param|empty|unknown]` — PASS
- AC4 — covered by the same test as AC1 (a goal on a later day comes first) — PASS
- AC5 — covered by `test_goal_list_shows_status_filter_links` — PASS
- AC6 — covered by `test_goal_list_marks_only_the_active_status_filter_link[no-param|planned|in-progress|done|unknown]` — PASS
- AC7 — covered by `test_goal_list_shows_filter_specific_empty_state_when_filter_matches_nothing` (filtered case) and `test_goal_list_shows_empty_state_when_user_has_no_goals` (unfiltered case) — PASS
- AC8 — covered by `test_filtered_goal_list_redirects_anonymous_visitors_to_login` — PASS

Full suite: 159 passed. `ruff check .`: all checks passed.

## Findings
- **Code review** (`code-reviewer`): 0 high, 0 medium, 4 low.
- **Security review** (`security-reviewer`): no findings.
  - Results stay scoped to `request.user` and login is still required.
  - `status` is checked against `Goal.Status` before it is used, and the query only goes through the ORM.
  - The raw parameter is never shown on the page, so there is no XSS risk.
  - `next` is unchanged and is protected by Django's allowed-host check.

The four low findings:
- [low] `src/apps/goals/views.py:22,29` — `status_filter()` is computed twice per request, once in `get_queryset` and once in `get_context_data`. — Optionally compute it once, for example with `cached_property`, if the helper gets more complex.
- [low] `src/apps/goals/tests/test_views.py:190-201` — The AC3 test only checks that every title is present. It does not check that the unfiltered or ignored-filter list stays newest first. — Give the goals different days and assert the order.
- [low] `src/apps/goals/tests/test_views.py:149` — The unfiltered empty-state test does not check that "No goals with status" is absent. — Add a negative assertion.
- [low] `src/apps/goals/tests/test_views.py:240-246` — The `aria-current` regex only looks inside `<a>` tags, so a stray `aria-current` on another element in the nav would go unnoticed. It does not hide any real failure. — No change needed.

None of these block the release. They are recorded as possible follow-ups.

## Reviewed
commit be46dbf, 2026-10-02
