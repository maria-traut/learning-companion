# Base layout and home page

## Story
As a visitor, I want a consistently styled home page at `/` with a nav bar, so that I know what Learning Companion is and every later page shares the same layout.

## Acceptance criteria
- [x] AC1 `GET /` returns 200 for an anonymous visitor (no login required).
- [x] AC2 The home page is rendered from `src/templates/base.html`, i.e. the response uses both `base.html` and the home page template that extends it.
- [x] AC3 `base.html` loads Pico.css from a CDN via a `<link rel="stylesheet">` pointing at a pinned Pico.css version.
- [x] AC4 `base.html` renders a `<nav>` containing the app name "Learning Companion" as a link to `/`.
- [x] AC5 `base.html` defines an overridable `title` block; the home page's `<title>` is "Home · Learning Companion", and a page that does not override it gets "Learning Companion".
- [x] AC6 `base.html` renders Django messages: a message added via `django.contrib.messages` appears in the next rendered page, and no messages container is rendered when there are none.
- [x] AC7 `base.html` renders a `<footer>` containing the app name.
- [x] AC8 The home page shows a heading and a short welcome text describing what Learning Companion does (tracking learning goals and sessions, attaching resources, AI summaries and next steps).
- [x] AC9 The existing smoke tests (system checks, admin login) still pass.

## Out of scope
- Login/logout/sign-up links and login state in the nav (#2).
- Nav links to Goals, Dashboard or other pages that don't exist yet (added by their tickets).
- Custom CSS, static assets, JavaScript, dark-mode toggles.
- Calls to action on the home page beyond the welcome text.

## Notes
Issue: #1

- Interview answers: short welcome on the home page; nav has brand link only (no dead links); base.html includes an overridable `<title>` block, a Django messages area and a footer.
- `TEMPLATES['DIRS']` already points at `src/templates/`; no project apps exist yet. Where the home view lives (new app vs. project URLconf) is a plan decision.
- `#2` builds on this layout (nav login state), `#20` expects `docker run` to serve this home page.
