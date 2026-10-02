# Profile model with focus areas, created automatically for every user

## Story
As a learner, I want a profile with my name, cohort and focus areas attached to my account from the moment it exists, so that later features (profile page, goals, AI summaries) can rely on it being there.

## Acceptance criteria
- [ ] AC1 A `Profile` is linked one-to-one to a `User` and reachable as `user.profile`; deleting the user deletes the profile.
- [ ] AC2 `Profile` has an optional free-text `name` and an optional free-text `cohort` (both default to empty), and a many-to-many `focus_areas` to `FocusArea` that may be empty.
- [ ] AC3 A `FocusArea` has a unique `name`; creating a second `FocusArea` with the same name raises `IntegrityError`, and `str(focus_area)` is its name.
- [ ] AC4 A profile can hold several focus areas, and one focus area can be shared by several profiles.
- [ ] AC5 A valid sign-up via `/accounts/signup/` creates exactly one profile for the new user, with empty `name`, empty `cohort` and no focus areas; the sign-up form itself is unchanged.
- [ ] AC6 Creating a user via `create_user` or `create_superuser` (i.e. admin, `createsuperuser`) also creates exactly one profile.
- [ ] AC7 Saving an existing user again does not create a second profile or fail.
- [ ] AC8 A data migration creates exactly one profile for every existing user who does not already have one, and leaves existing profiles unchanged.
- [ ] AC9 `str(profile)` is the user's username.
- [ ] AC10 `Profile` and `FocusArea` are registered in the admin. Their list and add pages load for a superuser. On a `Profile` admin page, a superuser can edit `name`, `cohort` and `focus_areas`.

## Out of scope
- Profile page where a user views/edits their own profile (#4).
- Any change to the sign-up form (no name/cohort/focus-area fields at sign-up).
- A fixed list of cohorts; seeding a predefined set of focus areas.
- Reusing `FocusArea` for LearningSession tags (#9 decides that).
- A custom user model.

## Notes
Issue: #3

- Interview answers (2026-10-02): focus areas are a separate `FocusArea` model (unique name, managed in admin) linked many-to-many from `Profile`; sign-up stays unchanged and the profile starts empty; every user gets a profile, however it is created, and existing users are backfilled; cohort is free text.
- Current state: the project uses the default `auth.User`; `apps.accounts` has views/urls/tests only (no models, admin or migrations yet). Sign-up is `SignUpView` with the stock `UserCreationForm` and does not log the user in.
- Database is SQLite by default, Postgres via `DATABASE_URL`, so no Postgres-only field types.
- The challenge (`instructions/challenge.md`) only requires a `Profile` linked to the user with `name`, `cohort` and a list of `focus_area` tags; auto-creation and admin registration come from this ticket.
