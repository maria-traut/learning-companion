import re
from datetime import UTC, datetime

import pytest
from django.utils.formats import date_format
from django.utils.timezone import localtime

from apps.goals.models import Goal

PASSWORD = "correct-horse-battery-9"
DESCRIPTION = "Work through the official tutorial."
EDITED = {"title": "Learn Flask", "description": "Build a small API.", "status": "done"}


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="ada", password=PASSWORD)


def template_names(response):
    return [template.name for template in response.templates]


def messages_text(response):
    container = re.search(
        r'<section id="messages"[^>]*>(.*?)</section>', response.content.decode(), re.DOTALL
    )
    return container.group(1) if container else ""


def nav_html(response):
    nav = re.search(r"<nav[^>]*>(.*?)</nav>", response.content.decode(), re.DOTALL)
    assert nav
    return nav.group(1)


def main_html(response):
    main = re.search(r"<main[^>]*>(.*?)</main>", response.content.decode(), re.DOTALL)
    assert main
    return main.group(1)


def tag_attributes(attrs):
    return {
        name: value
        for name, value in re.findall(r'([a-z_-]+)(?:="([^"]*)")?', attrs)
    }


def own_post_form(response):
    html = response.content.decode()
    forms = []
    for attrs, body in re.findall(r"<form([^>]*)>(.*?)</form>", html, re.DOTALL):
        attributes = tag_attributes(attrs)
        if attributes.get("method") == "post" and "action" not in attributes:
            forms.append(body)
    assert len(forms) == 1
    return forms[0]


def form_field_names(response):
    names = set(
        re.findall(r'<(?:input|select|textarea)[^>]*\bname="([^"]+)"', own_post_form(response))
    )
    return names - {"csrfmiddlewaretoken"}


def foreign_or_missing_goal_pk(django_user_model, case):
    if case == "missing":
        return 999_999
    grace = django_user_model.objects.create_user(username="grace", password=PASSWORD)
    return create_goal(grace, "Learn COBOL").pk


def create_goal(user, title, status=Goal.Status.PLANNED, day=1):
    goal = Goal.objects.create(
        user=user, title=title, description=DESCRIPTION, status=status
    )
    Goal.objects.filter(pk=goal.pk).update(created_at=datetime(2026, 1, day, tzinfo=UTC))
    goal.refresh_from_db()
    return goal


def test_goal_list_redirects_anonymous_visitors_to_login(client):
    response = client.get("/goals/")

    assert response.status_code == 302
    assert response.url == "/accounts/login/?next=/goals/"


@pytest.mark.django_db
def test_goal_list_renders_for_logged_in_users(client, user):
    client.force_login(user)

    response = client.get("/goals/")

    assert response.status_code == 200
    assert "goals/goal_list.html" in template_names(response)
    assert "base.html" in template_names(response)
    assert re.search(
        r"<title>\s*Goals · Learning Companion\s*</title>", response.content.decode()
    )


@pytest.mark.django_db
def test_goal_list_shows_title_status_and_created_date_newest_first(client, user):
    older = create_goal(user, "Learn Django", Goal.Status.IN_PROGRESS, day=3)
    newer = create_goal(user, "Learn SQL", Goal.Status.DONE, day=17)
    client.force_login(user)

    main = main_html(client.get("/goals/"))

    assert main.index("Learn SQL") < main.index("Learn Django")
    for goal, label in [(older, "In progress"), (newer, "Done")]:
        item = re.search(
            rf"<li[^>]*>((?:(?!</li>).)*{goal.title}(?:(?!</li>).)*)</li>", main, re.DOTALL
        )
        assert item, goal.title
        assert label in item.group(1)
        assert date_format(localtime(goal.created_at)) in item.group(1)


@pytest.mark.django_db
def test_goal_list_never_shows_another_users_goals(client, django_user_model, user):
    grace = django_user_model.objects.create_user(username="grace", password=PASSWORD)
    create_goal(user, "Learn Django")
    create_goal(grace, "Learn COBOL")
    client.force_login(user)

    main = main_html(client.get("/goals/"))

    assert "Learn Django" in main
    assert "Learn COBOL" not in main


@pytest.mark.django_db
def test_goal_list_shows_empty_state_when_user_has_no_goals(client, user):
    client.force_login(user)

    main = main_html(client.get("/goals/"))

    assert "No goals yet" in main


@pytest.mark.django_db
def test_goal_list_links_to_goal_create_page(client, user):
    client.force_login(user)

    main = main_html(client.get("/goals/"))

    assert re.search(r'<a href="/goals/new/"[^>]*>\s*New goal\s*</a>', main)


@pytest.mark.django_db
@pytest.mark.parametrize("logged_in", [True, False], ids=["logged-in", "anonymous"])
def test_nav_shows_goals_link_only_to_logged_in_users(client, user, logged_in):
    if logged_in:
        client.force_login(user)

    nav = nav_html(client.get("/"))

    has_goals_link = bool(re.search(r'<a href="/goals/"[^>]*>\s*Goals\s*</a>', nav))
    assert has_goals_link is logged_in


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["get", "post"])
def test_goal_create_redirects_anonymous_visitors_to_login(client, method):
    if method == "post":
        response = client.post(
            "/goals/new/", {"title": "Intruder", "description": DESCRIPTION}
        )
    else:
        response = client.get("/goals/new/")

    assert response.status_code == 302
    assert response.url == "/accounts/login/?next=/goals/new/"
    assert not Goal.objects.exists()


@pytest.mark.django_db
def test_goal_create_page_shows_title_description_and_status_fields(client, user):
    client.force_login(user)

    response = client.get("/goals/new/")

    assert response.status_code == 200
    assert "goals/goal_form.html" in template_names(response)
    assert "base.html" in template_names(response)
    assert form_field_names(response) == {"title", "description", "status"}
    assert re.search(r'<option value="planned"[^>]*\bselected\b', own_post_form(response))


@pytest.mark.django_db
def test_valid_goal_create_saves_goal_for_user_and_redirects_with_message(client, user):
    client.force_login(user)

    response = client.post(
        "/goals/new/",
        {"title": "Learn Django", "description": DESCRIPTION, "status": "in_progress"},
        follow=True,
    )

    assert response.redirect_chain == [("/goals/", 302)]
    assert "Goal created." in messages_text(response)
    goal = Goal.objects.get()
    assert (goal.user, goal.title, goal.description, goal.status) == (
        user,
        "Learn Django",
        DESCRIPTION,
        Goal.Status.IN_PROGRESS,
    )


@pytest.mark.django_db
def test_forged_owner_and_id_fields_cannot_touch_another_users_goal(
    client, django_user_model, user
):
    grace = django_user_model.objects.create_user(username="grace", password=PASSWORD)
    graces_goal = create_goal(grace, "Learn COBOL")
    client.force_login(user)

    response = client.post(
        "/goals/new/",
        {
            "title": "Learn Django",
            "description": DESCRIPTION,
            "status": "planned",
            "user": grace.pk,
            "id": graces_goal.pk,
            "pk": graces_goal.pk,
        },
    )

    assert response.status_code == 302
    adas_goal = Goal.objects.get(title="Learn Django")
    assert adas_goal.user == user
    assert adas_goal.pk != graces_goal.pk
    graces_goal.refresh_from_db()
    assert (graces_goal.user, graces_goal.title) == (grace, "Learn COBOL")
    assert Goal.objects.count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("data", "error"),
    [
        (
            {"title": "", "description": DESCRIPTION, "status": "planned"},
            "This field is required.",
        ),
        (
            {"title": "Learn Django", "description": "", "status": "planned"},
            "This field is required.",
        ),
        (
            {"title": "x" * 201, "description": DESCRIPTION, "status": "planned"},
            "at most 200 characters (it has 201)",
        ),
        (
            {"title": "Learn Django", "description": DESCRIPTION, "status": "archived"},
            "Select a valid choice. archived is not one of the available choices.",
        ),
    ],
    ids=["missing-title", "missing-description", "title-too-long", "unknown-status"],
)
def test_invalid_goal_create_rerenders_form_with_error_and_saves_nothing(
    client, user, data, error
):
    client.force_login(user)

    response = client.post("/goals/new/", data)

    assert response.status_code == 200
    assert "goals/goal_form.html" in template_names(response)
    assert error in response.content.decode()
    assert not Goal.objects.exists()


@pytest.mark.django_db
def test_goal_detail_redirects_anonymous_visitors_to_login(client, user):
    goal = create_goal(user, "Learn Django")

    response = client.get(f"/goals/{goal.pk}/")

    assert response.status_code == 302
    assert response.url == f"/accounts/login/?next=/goals/{goal.pk}/"


@pytest.mark.django_db
def test_goal_detail_renders_for_its_owner(client, user):
    goal = create_goal(user, "Learn Django")
    client.force_login(user)

    response = client.get(f"/goals/{goal.pk}/")

    assert response.status_code == 200
    assert "goals/goal_detail.html" in template_names(response)
    assert "base.html" in template_names(response)
    assert re.search(
        r"<title>\s*Learn Django · Learning Companion\s*</title>", response.content.decode()
    )


@pytest.mark.django_db
@pytest.mark.parametrize("case", ["other-user", "missing"])
def test_goal_detail_returns_404_for_another_users_or_missing_goal(
    client, django_user_model, user, case
):
    pk = foreign_or_missing_goal_pk(django_user_model, case)
    client.force_login(user)

    response = client.get(f"/goals/{pk}/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_goal_detail_shows_all_goal_fields(client, user):
    goal = create_goal(user, "Learn Django", Goal.Status.IN_PROGRESS, day=3)
    Goal.objects.filter(pk=goal.pk).update(updated_at=datetime(2026, 2, 14, tzinfo=UTC))
    goal.refresh_from_db()
    client.force_login(user)

    main = main_html(client.get(f"/goals/{goal.pk}/"))

    assert "Learn Django" in main
    assert DESCRIPTION in main
    assert "In progress" in main
    assert date_format(localtime(goal.created_at)) in main
    assert date_format(localtime(goal.updated_at)) in main


@pytest.mark.django_db
def test_goal_list_titles_link_to_their_detail_pages(client, user):
    goals = [create_goal(user, "Learn Django"), create_goal(user, "Learn SQL", day=2)]
    client.force_login(user)

    main = main_html(client.get("/goals/"))

    for goal in goals:
        assert re.search(
            rf'<a href="/goals/{goal.pk}/"[^>]*>\s*{re.escape(goal.title)}\s*</a>', main
        ), goal.title


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["get", "post"])
def test_goal_edit_redirects_anonymous_visitors_to_login(client, user, method):
    goal = create_goal(user, "Learn Django")
    url = f"/goals/{goal.pk}/edit/"

    response = client.post(url, EDITED) if method == "post" else client.get(url)

    assert response.status_code == 302
    assert response.url == f"/accounts/login/?next={url}"
    goal.refresh_from_db()
    assert (goal.title, goal.description, goal.status) == (
        "Learn Django",
        DESCRIPTION,
        Goal.Status.PLANNED,
    )
