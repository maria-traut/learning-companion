import pytest

PASSWORD = "correct-horse-battery-9"


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="ada", password=PASSWORD)


def test_goal_list_redirects_anonymous_visitors_to_login(client):
    response = client.get("/goals/")

    assert response.status_code == 302
    assert response.url == "/accounts/login/?next=/goals/"
