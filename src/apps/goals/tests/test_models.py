import pytest

from apps.goals.models import Goal

PASSWORD = "correct-horse-battery-9"


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="ada", password=PASSWORD)


def test_goal_displays_as_its_title():
    goal = Goal(title="Learn Django")

    assert str(goal) == "Learn Django"


@pytest.mark.django_db
def test_user_goals_contains_exactly_that_users_goals(django_user_model, user):
    grace = django_user_model.objects.create_user(username="grace", password=PASSWORD)
    django_goal = Goal.objects.create(user=user, title="Learn Django")
    sql_goal = Goal.objects.create(user=user, title="Learn SQL")
    cobol_goal = Goal.objects.create(user=grace, title="Learn COBOL")

    assert set(user.goals.all()) == {django_goal, sql_goal}
    assert set(grace.goals.all()) == {cobol_goal}
