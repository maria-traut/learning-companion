# Ticket backlog

Queue for `factory-manager`. One idea per line, top to bottom = priority order.
`factory-manager` owns the status marker, the ticket id, and the `[[parked: ...]]`
annotation on each line — add new ideas as plain `- [ ] <description>` lines and
leave the rest alone.

<!-- Project setup (Django scaffold, pytest, ruff, django-environ) was done outside the pipeline in the initial commit. -->

## Foundation
- [ ] Base layout and home page: `src/templates/base.html` with Pico.css from CDN, a nav bar, and a home page at `/` rendered from it
## Authentication and profile
- [ ] Sign up, log in and log out with Django's built-in auth views, using the base layout; nav shows login state (after base layout ships)
- [ ] Profile model linked one-to-one to the user with `name`, `cohort` and a list of `focus_area` tags, created automatically on sign-up and registered in the admin (after sign up/log in ships)
- [ ] Profile page where a logged-in user views and edits only their own profile; anonymous users are redirected to login (after profile model ships)
## Goals
- [ ] Goal model (`title`, `description`, `status` planned/in-progress/done, `created_at`, `updated_at`) owned by a user, with migration and admin (after sign up/log in ships)
- [ ] Goal list and create views, scoped so a user only sees and creates their own goals (after goal model ships)
- [ ] Goal detail, edit and delete views, returning 404 for other users' goals (after goal list/create ships)
- [ ] Filter the goal list by `status` via a query parameter (after goal list/create ships)
## Learning sessions
- [ ] LearningSession model linked to a Goal (`date`, `duration`, `notes`, `tags`), with migration and admin (after goal model ships)
- [ ] Learning session create, list, edit and delete views, reachable from the goal detail page and scoped to the goal owner (after learning session model and goal detail ship)
## Resource library
- [ ] Resource model linked to a Goal (`url`, `title`, `type` article/video/repo/doc), with migration and admin (after goal model ships)
- [ ] Form on the goal detail page to attach a resource to that goal, owner only (after resource model and goal detail ship)
- [ ] Show a goal's resources on its detail page, grouped or badged by `type` (after attach-resource form ships)
## AI summary and next steps
- [ ] OpenAI client service reading `OPENAI_API_KEY` via django-environ, with a function that sends chat messages and returns the reply text; fully mocked in tests (after goal detail ships)
- [ ] "Generate summary" action on the goal detail page that sends the goal's recent sessions and resources to OpenAI and displays the progress summary (after OpenAI client service and learning session views ship)
- [ ] "Suggest next steps" action on the goal detail page that asks OpenAI for 2-3 next learning actions and renders them as a list (after OpenAI client service ships)
## Dashboard and reporting
- [ ] Dashboard page showing the current user's goal count per `status` using ORM aggregation (after goal model ships)
- [ ] Dashboard table of total logged session hours per tag using ORM aggregation (after dashboard page and learning session model ship)
- [ ] Dashboard table of total logged session hours per week using ORM aggregation (after dashboard page and learning session model ship)
## Containerization and CI
- [ ] Dockerfile using the official Python image that serves the app with gunicorn; `docker build` + `docker run` serves the home page (after base layout ships)
- [ ] GitHub Actions workflow that installs dependencies and runs ruff and pytest on every push (after base layout ships)
