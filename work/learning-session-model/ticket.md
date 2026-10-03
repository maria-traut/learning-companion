# LearningSession model linked to a Goal, with migration and admin

## Story
As a learner, I want each study session I log to be stored against one of my goals with its date, duration, notes and tags, so that later features can list my sessions, summarise my progress and report hours per tag and per week.

## Acceptance criteria
- [ ] AC1 A new app `apps.learning_sessions` is installed (in `INSTALLED_APPS`), and its migrations apply cleanly (`migrate` and `makemigrations --check` report no pending changes).
- [ ] AC2 A `Tag` model has a `name` (max 50 characters) that is unique, lists in name order, and displays as its name.
- [ ] AC3 A `LearningSession` model has a foreign key `goal` to `goals.Goal` (`related_name="sessions"`), a `date`, a `duration_minutes` (positive integer), optional `notes` (blank allowed), and `tags` (many-to-many to `Tag`, `related_name="sessions"`).
- [ ] AC4 When no date is given, `date` defaults to today.
- [ ] AC5 `full_clean` rejects a `duration_minutes` of 0 or a negative number and accepts 1.
- [ ] AC6 `full_clean` requires a `goal` and a `date`, and accepts an empty `notes`.
- [ ] AC7 A session must have at least one tag: the session's admin form rejects a submission with no tags.
- [ ] AC8 Sessions list newest `date` first; sessions on the same date list most recently created first.
- [ ] AC9 A session displays as `"<goal title> – <date> (<duration> min)"`.
- [ ] AC10 Deleting a goal deletes its sessions; deleting a tag removes it from sessions and does not delete them. Deleting a user removes only that user's goals' sessions.
- [ ] AC11 Sessions and tags are many-to-many: one session can carry several tags, and one tag can be on several sessions, reachable through `tag.sessions`.
- [ ] AC12 Admin: `LearningSession` is registered with `list_display` goal, date, duration_minutes; a `list_filter` on date and tags; and a search over notes and the goal title. `Tag` is registered with search by name.

## Out of scope
- Create, list, edit and delete views and templates for sessions (#10).
- Showing sessions on the goal detail page (#10).
- Hours-per-tag and hours-per-week aggregation (#18, #19).
- Seeding default tags, and creating tags by free text in user-facing forms.
- Ownership checks in views. Ownership comes from `goal.user`, and #10 enforces it.

## Notes
Issue: #9

- Decisions from the interview:
  - The model gets its own app, `learning_sessions`. The name `sessions` clashes with `django.contrib.sessions`.
  - Tags are a many-to-many to a `Tag` model, following the `Profile` → `FocusArea` precedent. This keeps hours-per-tag a plain ORM group-by and works on both SQLite and Postgres.
  - Duration is stored as whole minutes, at least 1.
  - `date` defaults to today.
  - `notes` is optional.
- Tags were not chosen as optional, so a session needs at least one tag. Django does not check many-to-many fields in a model's `full_clean`, so this is enforced at the form level: the admin now (AC7), and the session forms in #10.
- "No future dates" was not chosen, so future dates are allowed.
- There are no factories and no conftest: the tests define their own `user`/goal fixtures, following the existing goals tests.
- The session has no direct `user` field; its owner is reached through `goal.user`.
