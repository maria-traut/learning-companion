# Sign up, log in and log out

## Story
As a learner, I want to create an account, log in and log out, so that my goals and sessions can be kept private to me.

## Acceptance criteria
- [ ] AC1 An anonymous visitor gets a sign-up page (200, rendered through `base.html`) with a form for username, password and password confirmation.
- [ ] AC2 A valid sign-up creates the user, does **not** log them in, redirects to the login page, and shows a success message ("Account created" or similar) there.
- [ ] AC3 An invalid sign-up (mismatched passwords, a username that is already taken, or a password the configured validators reject) re-renders the form with errors and creates no user.
- [ ] AC4 An anonymous visitor gets a login page (200, rendered through `base.html`) with a username/password form.
- [ ] AC5 A valid login authenticates the user, redirects to the home page, and shows a "Welcome, <username>" message.
- [ ] AC6 After login a safe, same-site `?next=` URL is honoured, and an external `?next=` URL is ignored in favour of the home page.
- [ ] AC7 Invalid credentials re-render the login form with an error, and the user stays anonymous.
- [ ] AC8 Logout via POST logs the user out, redirects to the home page, and shows a "You have been logged out" message. Logout via GET doesn't log the user out (Django returns 405).
- [ ] AC9 For anonymous visitors the nav shows "Log in" and "Sign up" links and no logout control.
- [ ] AC10 For logged-in users the nav shows their username and a logout button (a POST form with a CSRF token), and no "Log in" or "Sign up" links.
- [ ] AC11 A logged-in user who opens the login or sign-up page is redirected to the home page.
- [ ] AC12 `settings.LOGIN_URL` points at the login page, so later `login_required` views (#4 onwards) redirect there.
- [ ] AC13 Each rendered message includes its `message.tags` value as a CSS class in the message markup, and the messages container has `role="status"` so assistive technologies announce messages. This is deferred finding 6 from `work/base-layout/review.md`; the wording was clarified at plan approval.

## Out of scope
- Password reset by email, password change, and email addresses on the account.
- The profile model and profile page (#3, #4); creating a profile on sign-up is #3's job.
- A custom user model (the stock `auth.User` stays).
- Visual styling of message levels beyond exposing the tags in markup.

## Notes
Issue: #2

- Interview answers: after sign-up, redirect to login (no auto-login). The form is username + password only (Django's built-in user creation form and the existing password validators). Login and logout both redirect home. Include flash messages for sign-up, login and logout, plus message tags and `role="status"`.
- Use Django's built-in auth views (challenge.md: "Wire up the framework's built-in auth"). The challenge requires: "Confirm you can sign up, log out, and log back in."
- There are no auth settings or URLs yet. Django's default `LOGIN_URL` is `/accounts/login/`, and the default `LOGIN_REDIRECT_URL` (`/accounts/profile/`) doesn't exist, so it must be set.
- Since Django 5, logout is POST-only, so the nav's logout control has to be a form.
- AC11 (logged-in users redirected away from login and sign-up) is a default added during refinement. Remove it at approval if it's not wanted.
- #3 will hook profile creation into sign-up, so the sign-up flow should remain a single, obvious place to extend.
