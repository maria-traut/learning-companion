# Ticket backlog

Queue for `factory-manager`. One idea per line, top to bottom = priority order.
Each line mirrors a GitHub issue (`#<n>`) and its card on the project board
(https://github.com/users/maria-traut/projects/5): `[ ]` Todo, `[~]` In Progress,
`[x]` Done (on main). The pipeline skills own the status marker, the ticket id,
and the `[[parked: ...]]` annotation — add new ideas as `- [ ] #<issue> <description>`
(or plain `- [ ] <description>`; refine-ticket then creates the issue) and leave
the rest alone.

<!-- Project setup (Django scaffold, pytest, ruff, django-environ) was done outside the pipeline in the initial commit. -->

## Foundation
- [x] base-layout: #1 Base layout and home page: `src/templates/base.html` with Pico.css from CDN, a nav bar, and a home page at `/` rendered from it — see work/base-layout/review.md
## Authentication and profile
- [x] auth: #2 Sign up, log in and log out with Django's built-in auth views, using the base layout; nav shows login state (after base layout ships) — see work/auth/review.md
- [x] profile-model: #3 Profile model linked one-to-one to the user with `name`, `cohort` and a list of `focus_area` tags, created automatically on sign-up and registered in the admin (after sign up/log in ships) — see work/profile-model/review.md
- [x] profile-page: #4 Profile page where a logged-in user views and edits only their own profile; anonymous users are redirected to login (after profile model ships) — see work/profile-page/review.md
## Goals
- [x] goal-model: #5 Goal model (`title`, `description`, `status` planned/in-progress/done, `created_at`, `updated_at`) owned by a user, with migration and admin (after sign up/log in ships) — see work/goal-model/review.md
- [~] goal-list-create: #6 Goal list and create views, scoped so a user only sees and creates their own goals (after goal model ships)
- [ ] #7 Goal detail, edit and delete views, returning 404 for other users' goals (after goal list/create ships)
- [ ] #8 Filter the goal list by `status` via a query parameter (after goal list/create ships)
## Learning sessions
- [ ] #9 LearningSession model linked to a Goal (`date`, `duration`, `notes`, `tags`), with migration and admin (after goal model ships)
- [ ] #10 Learning session create, list, edit and delete views, reachable from the goal detail page and scoped to the goal owner (after learning session model and goal detail ship)
## Resource library
- [ ] #11 Resource model linked to a Goal (`url`, `title`, `type` article/video/repo/doc), with migration and admin (after goal model ships)
- [ ] #12 Form on the goal detail page to attach a resource to that goal, owner only (after resource model and goal detail ship)
- [ ] #13 Show a goal's resources on its detail page, grouped or badged by `type` (after attach-resource form ships)
## AI summary and next steps
- [ ] #14 OpenAI client service reading `OPENAI_API_KEY` via django-environ, with a function that sends chat messages and returns the reply text; fully mocked in tests (after goal detail ships)
- [ ] #15 "Generate summary" action on the goal detail page that sends the goal's recent sessions and resources to OpenAI and displays the progress summary (after OpenAI client service and learning session views ship)
- [ ] #16 "Suggest next steps" action on the goal detail page that asks OpenAI for 2-3 next learning actions and renders them as a list (after OpenAI client service ships)
## Dashboard and reporting
- [ ] #17 Dashboard page showing the current user's goal count per `status` using ORM aggregation (after goal model ships)
- [ ] #18 Dashboard table of total logged session hours per tag using ORM aggregation (after dashboard page and learning session model ship)
- [ ] #19 Dashboard table of total logged session hours per week using ORM aggregation (after dashboard page and learning session model ship)
## Containerization and CI
- [ ] #20 Dockerfile using the official Python image that serves the app with gunicorn; `docker build` + `docker run` serves the home page (after base layout ships)
- [ ] #21 GitHub Actions workflow that installs dependencies and runs ruff and pytest on every push (after base layout ships)
