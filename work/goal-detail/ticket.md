# Goal detail, edit and delete views scoped to the goal owner
## Story
As a logged-in learner, I want to open, edit and delete my own goals, so that I can keep them accurate, without anyone else being able to see or change them.
## Acceptance criteria
- [x] AC1 Anonymous GET to `/goals/<pk>/`, GET/POST to `/goals/<pk>/edit/` and GET/POST to `/goals/<pk>/delete/` redirect (302) to `/accounts/login/?next=<that url>`, and the goal is left unchanged.
- [x] AC2 The owner's GET to `/goals/<pk>/` returns 200, rendered with `goals/goal_detail.html` extending `base.html`, with page title "<goal title> · Learning Companion".
- [x] AC3 The detail page shows the goal's title, description, status label, created date and updated date.
- [x] AC4 The detail page links to `/goals/<pk>/edit/` and `/goals/<pk>/delete/`.
- [x] AC5 Each goal title on the goal list links to that goal's detail page.
- [x] AC6 The owner's GET to `/goals/<pk>/edit/` returns 200, rendered with `goals/goal_form.html`, with a single POST form whose fields are exactly `title`, `description` and `status`, pre-filled with the goal's current values.
- [x] AC7 A valid edit POST saves the new title, description and status, keeps the goal's owner, redirects to `/goals/<pk>/` and shows the message "Goal updated.".
- [x] AC8 Forged `user` / `id` / `pk` fields in the edit POST are ignored: the same goal is updated, it stays owned by the logged-in user, and other goals are unchanged.
- [x] AC9 An invalid edit POST (missing title, missing description, title over 200 characters, or unknown status) re-renders the form with 200, shows the error, and leaves the goal unchanged.
- [x] AC10 The owner's GET to `/goals/<pk>/delete/` returns 200, rendered with `goals/goal_confirm_delete.html` extending `base.html`, asking to confirm deleting the goal by title, with a single POST form.
- [x] AC11 The owner's POST to `/goals/<pk>/delete/` deletes the goal, redirects to `/goals/` and shows the message "Goal deleted.".
- [x] AC12 For a goal owned by another user, a logged-in GET to the detail, edit and delete URLs and a POST to the edit and delete URLs all return 404, and that goal is left unchanged (not edited, not deleted).
- [x] AC13 For a nonexistent pk, the logged-in detail, edit and delete URLs return 404.
## Out of scope
- Filtering the list by status (#8).
- Learning sessions or resources on the detail page (#10, #12, #13).
- A custom 404 template.
- Soft delete or undo.
## Notes
Issue: #7

- Interview answers:
  - The detail page shows all fields plus Edit and Delete links, and the list titles link to it.
  - Edit redirects to the detail page with "Goal updated.".
  - Delete uses a confirmation page: GET shows it, POST deletes and redirects to the list with "Goal deleted.".
  - All detail, edit and delete requests (GET and POST) for another user's goal return 404.
- The edit form uses the same fields as the create form (`title`, `description`, `status`). `goals/goal_form.html` is shared with create; its heading/title may differ per view.
- Follow the goal-list-create patterns: class-based views with `LoginRequiredMixin`, ownership scoped through `request.user.goals`, the `GoalForm` field list, and `SuccessMessageMixin`.
- These are the project's first 404 tests. There is no custom `404.html`, so Django's default page is used.
- Anonymous visitors are redirected to login before any ownership check, so they never learn whether a goal exists.
