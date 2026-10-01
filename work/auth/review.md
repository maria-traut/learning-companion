# Review: auth

## Verdict: PASS

No high or medium findings from either reviewer. Every acceptance criterion is proven by a passing test, and the suite is green.

## Acceptance criteria
All tests are in `src/apps/accounts/tests/test_views.py` unless noted.
- AC1 — `test_signup_page_is_served_to_anonymous_visitors` — PASS
- AC2 — `test_valid_signup_creates_user_and_redirects_to_login_without_logging_in`, `test_signup_shows_account_created_message_on_login_page` — PASS
- AC3 — `test_invalid_signup_rerenders_form_with_error_and_creates_no_user[mismatched-passwords|username-taken|weak-password]` — PASS
- AC4 — `test_login_page_is_served_to_anonymous_visitors` — PASS
- AC5 — `test_valid_login_redirects_home_and_authenticates`, `test_login_shows_welcome_message` — PASS
- AC6 — `test_login_follows_only_safe_next_url[same-site|external]` — PASS
- AC7 — `test_login_with_wrong_password_shows_error_and_stays_anonymous` — PASS
- AC8 — `test_logout_via_post_logs_out_and_redirects_home`, `test_logout_shows_logged_out_message_on_home_page`, `test_logout_via_get_is_not_allowed_and_keeps_user_logged_in` — PASS
- AC9 — `test_nav_offers_login_and_signup_to_anonymous_visitors` — PASS
- AC10 — `test_nav_shows_username_and_logout_form_to_logged_in_users` — PASS (username assertion is weak, finding 3)
- AC11 — `test_logged_in_user_is_redirected_home_from_login_page`, `test_logged_in_user_is_redirected_home_from_signup_page` — PASS
- AC12 — `test_login_url_setting_points_at_login_page` — PASS
- AC13 — `tests/test_base_layout.py::test_base_layout_renders_message_tags_as_css_classes`, `::test_base_layout_messages_container_is_a_status_region` — PASS

Suite: 36 passed. `ruff check .` clean. `manage.py check` clean.

## Findings
Code review:
1. [low, process] work/auth/activity.log — The characterization steps (3, 6, 9, 10, 13) show only green test writes. The temporary breakage that proved each test can fail was done with shell `sed`/`git checkout`, so the hook never logged it. The red runs are in the session output but not in the audit trail. — For future characterization checks, make the temporary break with Edit (and revert with Edit), so the hook records the red.
2. [low] work/auth/plan.md — The design bullet still claimed `LOGIN_URL` is set explicitly. — **Fixed in this review** (artifact text only, no code): the bullet now says the Django default is relied on deliberately.
3. [low] src/apps/accounts/tests/test_views.py:205 — `assert "ada" in nav` could rarely match the random CSRF token. — Assert structurally, e.g. `<li>\s*ada\s*</li>`.
4. [low] src/apps/accounts/tests/test_views.py:15-19 — `messages_text` duplicates the `#messages` regex that now lives in `tests/test_base_layout.py::messages_container`, and it returns `""` instead of asserting. — Share one asserting helper, e.g. in a `conftest.py` or test utility module.
5. [low] src/apps/accounts/tests/test_views.py:22-30 — The `user` fixture sits between helpers. — Group fixtures and helpers.
6. [low] src/apps/accounts/views.py:32-36 — "You have been logged out." is also shown to an already anonymous user who POSTs to logout. — Optionally add the message only if the user was authenticated before `super().post()`.
7. [low] src/apps/accounts/tests/test_views.py:126-133 — AC6 doesn't pin the scheme-relative `//evil.example.com/` case. Django already handles it. — Optionally add it as a third case.

Security review:
8. [low] src/apps/accounts/views.py:11 — Sign-up reveals whether a username exists. This is inherent to username sign-up, and login's error is generic. — Accept. Consider rate limiting with finding 9.
9. [low] src/apps/accounts/urls.py:9 — No brute-force protection on login (the admin login has the same gap). — Candidate for its own ticket (e.g. django-axes or proxy rate limiting).
10. [low] src/config/settings.py:31 — The `SECRET_KEY` falls back to an insecure default. This predates the branch, but it now signs auth sessions. — Deployment ticket: require it when `DEBUG=False`.
11. [low] src/config/settings.py — No `SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE`/`SECURE_SSL_REDIRECT`/HSTS. This predates the branch. — Deployment ticket. Check with `manage.py check --deploy`.

None of these block release. Findings 3–7 are test and UX polish, 9–11 are production hardening outside this ticket's scope, and 8 is accepted. They are recorded here as candidates for follow-up backlog items. Confirmed sound: open-redirect handling (`next` is validated by Django and sign-up never reads it), CSRF on all three POST forms, POST-only logout, autoescaping of the username and message tags, session rotation on login and flush on logout, and that the password validators are applied.

## Reviewed
commit 1318a8c, 2026-10-01
