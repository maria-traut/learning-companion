# Goal list and create views scoped to the logged-in user
## Story
As a logged-in learner, I want to see a list of my own learning goals and create new ones, so that I can keep track of what I'm working towards without seeing anyone else's goals.
## Acceptance criteria
- [ ] AC1 An anonymous GET to `/goals/` redirects (302) to `/accounts/login/?next=/goals/`.
- [ ] AC2 An anonymous GET or POST to `/goals/new/` redirects (302) to `/accounts/login/?next=/goals/new/`, and the POST creates no goal.
- [ ] AC3 A logged-in GET to `/goals/` returns 200, rendered with `goals/goal_list.html` extending `base.html`, with page title "Goals · Learning Companion".
- [ ] AC4 The goal list shows each of the user's goals with its title, status label (e.g. "In progress") and created date, newest first.
- [ ] AC5 The goal list never shows another user's goals.
- [ ] AC6 When the user has no goals, the list shows an empty-state message.
- [ ] AC7 The goal list page links to `/goals/new/`.
- [ ] AC8 A logged-in GET to `/goals/new/` returns 200, rendered with `goals/goal_form.html` extending `base.html`, with a single POST form whose fields are exactly `title`, `description` and `status`; status defaults to Planned.
- [ ] AC9 A valid POST to `/goals/new/` creates one goal owned by the logged-in user with the submitted title, description and status, redirects to `/goals/` and shows the message "Goal created.".
- [ ] AC10 Forged `user` / `id` / `pk` fields in the create POST are ignored: the goal is still owned by the logged-in user.
- [ ] AC11 An invalid POST (missing title, missing description, title over 200 characters, or unknown status) re-renders the form with 200, shows the error, and creates no goal.
- [ ] AC12 The nav bar shows a "Goals" link to `/goals/` for logged-in users and not for anonymous visitors.
## Out of scope
- Goal detail, edit and delete views (#7).
- Filtering the list by status (#8).
- Pagination.
- Making `description` optional (model stays as is).
## Notes
Issue: #6

- Interview answers: form fields are title, description, status (status defaults to Planned; description stays required, as in the model); after create, redirect to the goal list with a "Goal created." success message; list items show title, status and created date with no pagination; nav gets a "Goals" link for logged-in users only.
- Goals don't link to a detail page yet because the detail page arrives in #7.
- Follow the accounts/profile pattern: class-based views with `LoginRequiredMixin`, a `ModelForm` with an explicit field list that never includes `user`, app templates under `goals/templates/goals/`, and `SuccessMessageMixin`.
- `LOGIN_URL` is Django's default `/accounts/login/`. The goals URLs are not wired into `config/urls.py` yet.
