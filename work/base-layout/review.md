# Review: base-layout

## Verdict: FAIL

Reason: AC6 and AC8 are only partially covered by their tests (see findings 1 and 2). The suite is green and no finding is high severity, but an AC without full test coverage means FAIL.

## Acceptance criteria
- AC1 — `src/apps/pages/tests/test_views.py::test_home_page_is_served_to_anonymous_visitors` — PASS
- AC2 — `src/apps/pages/tests/test_views.py::test_home_page_extends_base_layout` — PASS
- AC3 — `tests/test_base_layout.py::test_base_layout_links_pinned_pico_css_from_cdn` — PASS (test is brittle, finding 3)
- AC4 — `tests/test_base_layout.py::test_base_layout_nav_links_app_name_to_home` — PASS
- AC5 — `tests/test_base_layout.py::test_base_layout_has_default_title`, `src/apps/pages/tests/test_views.py::test_home_page_title` — PASS
- AC6 — `tests/test_base_layout.py::test_base_layout_renders_messages`, `::test_base_layout_omits_messages_container_without_messages` — PARTIAL: renders within the same request only, and "appears in the next rendered page" is not proven (finding 1)
- AC7 — `tests/test_base_layout.py::test_base_layout_has_footer_with_app_name` — PASS
- AC8 — `src/apps/pages/tests/test_views.py::test_home_page_shows_welcome_heading_and_text` — PARTIAL: "next steps" is not asserted, and the topics are matched anywhere in the page rather than in the welcome text (finding 2)
- AC9 — `tests/test_smoke.py` (2 tests) — PASS

Suite: 12 passed. `ruff check .` clean. `manage.py check` clean.

## Findings
1. [medium] tests/test_base_layout.py:41-50 — AC6 requires the message to appear in the *next* rendered page. The test only renders `base.html` in the request that added the message, so message storage and middleware across a redirect are never exercised. — Add a client-level test: a test-only view adds a message and redirects to `/`, then assert the message is inside `#messages` after following the redirect.
2. [low → blocks AC8] src/apps/pages/tests/test_views.py:24-30 — "next steps" is never asserted, the topics are searched in the whole response, and `<h1>.+</h1>` accepts any heading. — Scope the assertions to the `<main>` content and add "next steps".
3. [low] tests/test_base_layout.py:20-24 — The Pico regex depends on attribute order and an exact tag shape, so adding `integrity`/`crossorigin` breaks it. — Locate the `<link>` tag, then assert `rel="stylesheet"` and the pinned `href` independently.
4. [low, security] src/templates/base.html:7 — The CDN stylesheet has no Subresource Integrity. — Add `integrity="sha384-…"` for pico 2.1.1 and `crossorigin="anonymous"`.
5. [low] tests/test_base_layout.py:41,53 — `@pytest.mark.django_db` isn't needed (no DB access). — Remove it.
6. [low] src/templates/base.html:20-22 — Messages render without `message.tags` or `role="status"`. — Not required by any AC. **Deferred**: it fits naturally with the first ticket that actually emits messages (#2 auth).
7. [low] src/apps/pages/apps.py:5, src/config/urls.py:22 — Quoting is mixed: single quotes come from the Django templates. — **Deferred**: it belongs to a repo-wide formatter decision (`ruff format` / `Q` rules), which is out of scope for this ticket.

Out of diff (security reviewer, informational): the `SECRET_KEY` default and the missing production `SECURE_*` settings belong to a deployment ticket.

## Reviewed
commit e15222a, 2026-10-01
