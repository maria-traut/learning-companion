import re

import pytest

from apps.goals.models import Goal

PASSWORD = "correct-horse-battery-9"
DESCRIPTION = "Work through the official tutorial."


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="ada", password=PASSWORD)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url",
    ["/admin/goals/goal/", "/admin/goals/goal/add/"],
    ids=["goal-list", "goal-add"],
)
def test_admin_goal_pages_load_for_a_superuser(admin_client, url):
    response = admin_client.get(url)

    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_goal_list_shows_title_owner_status_and_timestamps(admin_client, user):
    Goal.objects.create(user=user, title="Learn Django", description=DESCRIPTION)

    page = admin_client.get("/admin/goals/goal/").content.decode()

    for field in ("title", "user", "status", "created_at", "updated_at"):
        assert re.search(rf'<th scope="col"[^>]*class="[^"]*\bcolumn-{field}\b', page), field
