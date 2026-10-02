import re

import pytest

PASSWORD = "correct-horse-battery-9"


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="ada", password=PASSWORD)


def template_names(response):
    return [template.name for template in response.templates]


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
