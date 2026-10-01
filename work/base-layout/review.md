# Review: base-layout

## Verdict: PASS

Round 2. Round 1 failed because AC6 and AC8 were only partially covered (history below). Plan steps 11–15 fixed all five planned findings. Both reviewers now report 0 high and 0 medium findings, every AC has a test that can fail, and the suite is green.

## Acceptance criteria
- AC1 — `src/apps/pages/tests/test_views.py::test_home_page_is_served_to_anonymous_visitors` — PASS
- AC2 — `src/apps/pages/tests/test_views.py::test_home_page_extends_base_layout` — PASS
- AC3 — `tests/test_base_layout.py::test_base_layout_links_pinned_pico_css_from_cdn`, `::test_base_layout_pico_link_has_subresource_integrity` — PASS
- AC4 — `tests/test_base_layout.py::test_base_layout_nav_links_app_name_to_home` — PASS
- AC5 — `tests/test_base_layout.py::test_base_layout_has_default_title`, `src/apps/pages/tests/test_views.py::test_home_page_title` — PASS
- AC6 — `tests/test_base_layout.py::test_base_layout_renders_messages`, `::test_message_added_in_one_request_appears_on_next_page`, `::test_base_layout_omits_messages_container_without_messages` — PASS
- AC7 — `tests/test_base_layout.py::test_base_layout_has_footer_with_app_name` — PASS
- AC8 — `src/apps/pages/tests/test_views.py::test_home_page_shows_welcome_heading_and_text` — PASS
- AC9 — `tests/test_smoke.py::test_django_system_checks_pass`, `::test_admin_login_page_is_served` — PASS

Suite: 14 passed. `ruff check .` clean. `manage.py check` clean. The Pico 2.1.1 SRI hash was checked against the files served by jsDelivr and unpkg (implementation), and independently by the code reviewer.

## Findings (round 2)
1. [low] tests/test_base_layout.py:80 — The redirect test runs without DB access only because the default `FallbackStorage` keeps messages in a cookie. If storage moves to sessions, the test will error loudly on DB access. — Add `@pytest.mark.django_db` when session-backed message storage is introduced.
2. [low] tests/test_base_layout.py:75, 85-87 — The `#messages` section regex is duplicated. — Extract a helper like `pico_link_tag` the next time these tests change.
3. [low] src/apps/pages/tests/test_views.py:29 — `<h1>` is matched without attributes. — Use `<h1[^>]*>`, consistent with the other element regexes.
4. [low, process] work/base-layout/activity.log — The hook log doesn't show the red runs. Most test edits were made through shell heredocs and scripts rather than the Write/Edit tools, so the post-write hook never fired for them. The red runs did happen and were checked in-session: each step's test failed on its assertion before implementation, and steps 11–13 were verified by temporarily breaking the behaviour. But the audit trail doesn't record them. — From now on, make source and test writes with Write/Edit so the hooks record them. Optionally, have the post-write hook also watch Bash writes under `src/` and `tests/`.

None of these block release. Findings 1–3 are minor maintainability points and don't justify another implementation round. Finding 4 is a process lesson for the next tickets.

Security: 0 findings. SRI is present and well-formed, auto-escaping is intact, and the test-only URLconf is used only via `@pytest.mark.urls` and is unreachable from `config.urls`. Out of diff: the `SECRET_KEY` fallback and production `SECURE_*` settings belong to a deployment ticket.

## Round 1 (history)
Verdict FAIL at commit e15222a. AC6 was not proven across requests, and AC8 didn't check "next steps" and searched the whole page. Further findings: a brittle Pico regex, missing SRI, and unneeded `django_db` markers. All five were fixed by plan steps 11–15. Deferred with rationale: message tags and `role="status"` (goes with #2) and repo-wide quote style (formatter decision).

## Reviewed
commit 55e5329, 2026-10-01
