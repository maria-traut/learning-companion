import pytest


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url",
    ["/admin/goals/goal/", "/admin/goals/goal/add/"],
    ids=["goal-list", "goal-add"],
)
def test_admin_goal_pages_load_for_a_superuser(admin_client, url):
    response = admin_client.get(url)

    assert response.status_code == 200
