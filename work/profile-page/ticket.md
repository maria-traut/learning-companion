# Profile page where a logged-in user views and edits their own profile

## Story
As a logged-in learner, I want to see and edit my own name, cohort and focus areas, so that my profile reflects what I am learning, without anyone else being able to see or change it.

## Acceptance criteria
- [x] AC1 An anonymous `GET` to `/accounts/profile/` or `/accounts/profile/edit/` redirects to `/accounts/login/?next=<that path>`. An anonymous `POST` to `/accounts/profile/edit/` also redirects to login and changes no profile.
- [x] AC2 A logged-in `GET /accounts/profile/` returns 200 and shows the user's username, name, cohort and the names of their focus areas.
- [x] AC3 The profile page shows only the logged-in user's data. When two users have different names, cohorts and focus areas, each user's page shows their own values and none of the other user's.
- [x] AC4 The profile page links to `/accounts/profile/edit/`.
- [x] AC5 A logged-in `GET /accounts/profile/edit/` returns 200 with a form pre-filled with the user's current `name` and `cohort`. It has one checkbox per existing `FocusArea`, and the user's current focus areas are checked.
- [x] AC6 A valid `POST` to `/accounts/profile/edit/` saves the new `name`, `cohort` and focus areas to the user's own profile, replacing the previous set (unticking everything clears it). It redirects to `/accounts/profile/`, and the page then shows "Profile updated" in the messages area.
- [x] AC7 The form has exactly three editable fields: `name`, `cohort` and `focus_areas`. Submitted values or extra fields cannot change the profile owner or modify anyone else's profile.
- [x] AC8 An invalid `POST` re-renders the form with 200 and an error and saves nothing. Invalid means a `name` or `cohort` longer than 100 characters, or a focus area id that doesn't exist.
- [x] AC9 When no `FocusArea` exists, the edit page says that no focus areas are available yet, and saving `name` and `cohort` still works.
- [x] AC10 A logged-in user who has no profile row gets exactly one empty profile created when they open the profile page or the edit page, and the page returns 200.
- [x] AC11 For a logged-in user, the username in the nav is a link to `/accounts/profile/`. Anonymous visitors see no link to `/accounts/profile/`.

## Out of scope
- Changing the username, email or password.
- Viewing other users' profiles, or public profiles.
- Creating new focus areas from the profile form; seeding a starter set (focus areas stay admin-managed, as in #3).
- Changing `LOGIN_REDIRECT_URL` (login still lands on the home page).
- Deleting the account or the profile.

## Notes
Issue: #4

- Interview answers (2026-10-02):
  - There is a read-only page at `/accounts/profile/` and an edit page at `/accounts/profile/edit/`. Saving redirects to the read-only page with a "Profile updated" message.
  - Focus areas are checkboxes over the existing, admin-managed `FocusArea`s.
  - A missing profile is created when the user opens either page.
  - The nav's username becomes the profile link.
- The URLs carry no ids: both always mean the logged-in user's own profile, so there is no other user's object to reach. CLAUDE.md's "another user's object returns 404" convention therefore becomes AC3 (only own data shown) and AC7 (a forged `user` or extra fields can't touch another profile).
- Current state (from #3):
  - `Profile` (`name`, `cohort` CharField(100, blank); `focus_areas` M2M to `FocusArea`, blank) is auto-created by a `post_save` signal.
  - Sign-up is not atomic, so a user without a profile is possible (AC10).
  - No `FocusArea` rows are seeded (AC9).
  - There are no ModelForms or `LoginRequiredMixin` views in the project yet.
  - `/accounts/profile/` is free; `LOGIN_URL` is the default `/accounts/login/`.
- Challenge requirement (`instructions/challenge.md`): "the profile page only shows your own data".
