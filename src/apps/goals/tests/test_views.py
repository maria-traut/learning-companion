import re
from datetime import UTC, datetime

import pytest
from django.utils.formats import date_format
from django.utils.timezone import localtime

from apps.goals.models import Goal

PASSWORD = "correct-horse-battery-9"
DESCRIPTION = "Work through the official tutorial."


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="ada", password=PASSWORD)


def template_names(response):
    return [template.name for template in response.templates]


def main_html(response):
    main = re.search(r"<main[^>]*>(.*?)</main>", response.content.decode(), re.DOTALL)
    assert main
    return main.group(1)


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
