# Review: profile-page
## Verdict: PASS

Round 2, after the round-1 findings were implemented as plan steps 16–20.
- The suite is green (79 passed). `ruff check .`, `manage.py check` and `makemigrations --check` are clean.
- Neither reviewer found any high- or medium-severity issue.
- Every acceptance criterion is covered by a test that was shown to fail when the behaviour breaks.
- The code reviewer confirmed all five round-1 findings turned into steps are fixed.
- Production code is unchanged since round 1: `git diff e03cf0f..HEAD -- src` touches only `src/apps/accounts/tests/test_views.py`.

## Acceptance criteria
- AC1: covered by `test_profile_page_redirects_anonymous_visitors_to_login` and `test_profile_edit_page_redirects_anonymous_visitors_to_login` (get, post). PASS
- AC2: covered by `test_profile_page_shows_the_users_own_details` (exact `<dl>` values) and `test_empty_profile_page_shows_placeholders`. PASS
- AC3: covered by `test_profile_page_shows_only_the_logged_in_users_data`. It checks exact `<dl>` values per user, and that the other user's name and cohort appear nowhere in `<main>`. PASS
- AC4: covered by `test_profile_page_links_to_the_edit_page`. PASS
- AC5: covered by `test_profile_edit_form_is_prefilled_with_a_checkbox_per_focus_area`. PASS
- AC6: PASS. Covered by these three tests:
  - `test_valid_profile_edit_saves_replaces_focus_areas_and_redirects`
  - `test_profile_edit_with_no_focus_areas_ticked_clears_them`
  - `test_profile_edit_shows_profile_updated_message_on_profile_page`
- AC7: covered by `test_profile_edit_form_has_exactly_name_cohort_and_focus_areas` and `test_forged_owner_and_extra_fields_cannot_touch_another_profile`. PASS
- AC8: covered by `test_invalid_profile_edit_rerenders_form_with_error_and_saves_nothing` (3 cases). PASS
- AC9: covered by `test_profile_edit_without_focus_areas_says_so_and_still_saves` and `test_profile_edit_with_focus_areas_does_not_claim_there_are_none`. It is now pinned both ways. PASS
- AC10: covered by `test_profile_pages_create_a_missing_profile_on_the_spot` (2 URLs). PASS
- AC11: covered by `test_nav_username_links_logged_in_users_to_their_profile` and `test_nav_has_no_profile_link_for_anonymous_visitors`. PASS

## Findings
Code review found 0 high, 0 medium and 5 low. Security review found 0 high, 0 medium and no new findings; it re-checked access control, mass assignment, CSRF, XSS, open redirect, authn and secrets.

All of the lows below concern how strict the test helpers are. None of them makes a current test wrong or able to pass vacuously, so they are left as follow-ups and do not block release:
- [low] `src/apps/accounts/tests/test_views.py:58`: `tag_attributes` only handles lowercase, digit-free names with double-quoted values. Single quotes or uppercase would mis-parse, though Django's widget output never produces them. Recommendation: widen the pattern or use the stdlib `html.parser`, ideally together with moving the helpers into a `conftest.py` (the follow-up deferred from #3).
- [low] `src/apps/accounts/tests/test_views.py:50`: `profile_values` matches values by position, not by their `<dt>` label. Recommendation: return label/value pairs.
- [low] `src/apps/accounts/tests/test_views.py:404-405`: the AC5 pre-fill regexes for `name` and `cohort` still depend on attribute order, which is inconsistent with the step-19 helpers. Recommendation: read those inputs through `tag_attributes`.
- [low] `src/apps/accounts/tests/test_views.py:550`: the step-16 absence test doesn't also check for 200 or the edit template. Recommendation: add both so the absence is tied to a real edit page.
- [low] `src/apps/accounts/tests/test_views.py:70`: `\bname="` also matches `data-name="..."`. That would fail loudly, not pass falsely. Recommendation: use a stricter lookbehind or `tag_attributes`.

Carried over from round 1 and still accepted, with both reviewers agreeing:
- the sign-up test refactor, recorded for the audit trail
- the GET-time `get_or_create`, which AC10 requires

Also carried over: the pre-existing `SECRET_KEY` fallback in `src/config/settings.py:31` is recommended as a separate ticket before #20/#21.

## Reviewed
commit 8a16f32, 2026-10-02

---

## Round 1 (history)
### Verdict: FAIL

The checks are clean:
- the suite is green (77 passed)
- `ruff check .`, `manage.py check` and `makemigrations --check` are clean
- neither reviewer found a high-severity issue

The verdict is FAIL because AC9 is only partly covered, the same standard as #3's round 1. The test pins that the notice appears when no focus areas exist. Nothing pins that it is absent when they do exist. Inverting or removing the `{% if %}` in `profile_form.html:7`, so the notice always shows, would leave the suite green, even though the page would then wrongly claim there are no focus areas.

### Acceptance criteria
- **AC1**: PASS. Covered by `test_profile_page_redirects_anonymous_visitors_to_login` and `test_profile_edit_page_redirects_anonymous_visitors_to_login` (`get` and `post` cases).
- **AC2**: PASS. Covered by `test_profile_page_shows_the_users_own_details`. Its checks are broad substring checks; see the low finding.
- **AC3**: PASS. Covered by `test_profile_page_shows_only_the_logged_in_users_data`, which was also checked with a temporary break.
- **AC4**: PASS. Covered by `test_profile_page_links_to_the_edit_page`.
- **AC5**: PASS. Covered by `test_profile_edit_form_is_prefilled_with_a_checkbox_per_focus_area`.
- **AC6**: PASS. Covered by these three tests:
  - `test_valid_profile_edit_saves_replaces_focus_areas_and_redirects`
  - `test_profile_edit_with_no_focus_areas_ticked_clears_them`
  - `test_profile_edit_shows_profile_updated_message_on_profile_page`
- **AC7**: PASS. Covered by `test_profile_edit_form_has_exactly_name_cohort_and_focus_areas` and `test_forged_owner_and_extra_fields_cannot_touch_another_profile`.
- **AC8**: PASS. Covered by `test_invalid_profile_edit_rerenders_form_with_error_and_saves_nothing` (3 cases).
- **AC9**: **PARTIAL.** `test_profile_edit_without_focus_areas_says_so_and_still_saves` covers the case with no focus areas. Nothing checks that the notice is absent when focus areas exist.
- **AC10**: PASS. Covered by `test_profile_pages_create_a_missing_profile_on_the_spot` (2 URLs).
- **AC11**: PASS. Covered by `test_nav_username_links_logged_in_users_to_their_profile` and `test_nav_has_no_profile_link_for_anonymous_visitors`.

### Findings
Code review (`code-reviewer`) found 0 high, 1 medium and 5 low. Security review (`security-reviewer`) found 0 high, 0 medium and 1 low. The security review found no problems in any of these areas:
- IDOR (both URLs are id-free, and `get_object` never reads request data)
- mass assignment (explicit form fields, forged `user`/`pk`/`id` ignored)
- CSRF (middleware on, token in the form)
- XSS (everything autoescaped, no `|safe` or `mark_safe`)
- open redirect (fixed `success_url`, `next` handled by Django's safe-URL check)
- authentication (`LoginRequiredMixin` first in both views)

Turned into plan steps (16–20):
- [medium] `src/apps/accounts/tests/test_views.py:479`. The AC9 notice is only checked for presence, never for absence when focus areas exist. **Recommendation:** assert the notice is absent when at least one focus area exists. Plan step 16.
- [low] `src/apps/accounts/templates/accounts/profile_detail.html:11,13,19`. The "Not set yet" and "No focus areas yet" fallbacks are not test-driven (disclosed). Removing them would make empty profiles show blank values unnoticed. **Recommendation:** add a test for an empty profile. Plan step 17.
- [low] `src/apps/accounts/tests/test_views.py:298,313`. The AC2/AC3 checks are case-sensitive substring checks on short tokens ("ada", "sql") against all of `<main>`, which also contains the messages section. They are correct today but fragile. **Recommendation:** scope the checks to the profile's `<dd>` values. Plan step 18.
- [low] `src/apps/accounts/tests/test_views.py:45,52`. `form_field_names` matches the literal `<form method="post">`, and `focus_area_checkboxes` depends on Django's attribute order. **Recommendation:** make both independent of attribute order, without matching the nav's logout form. Plan step 19.
- [low] `src/apps/accounts/tests/test_views.py:507`. The anonymous edit-page test sits at the end of the file, away from its profile-page counterpart at line 290. **Recommendation:** move it next to that test. Plan step 20.

Recorded and deliberately not turned into steps:
- [low] (code) `src/apps/accounts/tests/test_views.py:123`: in step 7, the #3 sign-up form test was refactored to use the new `form_field_names` helper. This refactor was not listed in the plan and was bundled into a `test(...)` commit instead of its own `refactor` step. It is recorded here for the audit trail. The behaviour is unchanged and the test still pins the exact set of sign-up fields.
- [low] (security) `src/apps/accounts/views.py:45`: a GET can write a missing profile row through `get_or_create`. This is accepted, because AC10 requires it. It only ever creates the requester's own empty row, and `get_or_create` handles concurrent inserts.
- [info] (security, pre-existing, not part of this diff) `src/config/settings.py:31`: `SECRET_KEY` falls back to `'django-insecure-dev-only-change-me'`. Recommendation for a separate ticket: require `SECRET_KEY` outside development, for example before the Docker/CI tickets #20 and #21.

### Reviewed
commit e03cf0f, 2026-10-02
