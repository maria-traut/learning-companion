import pytest
from django.core.exceptions import ValidationError

from apps.goals.models import Goal

PASSWORD = "correct-horse-battery-9"
DESCRIPTION = "Work through the official tutorial."


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


@pytest.mark.django_db
def test_deleting_a_user_deletes_only_their_goals(django_user_model, user):
    grace = django_user_model.objects.create_user(username="grace", password=PASSWORD)
    adas_goal = Goal.objects.create(user=user, title="Learn Django")
    graces_goal = Goal.objects.create(user=grace, title="Learn COBOL")

    user.delete()

    assert not Goal.objects.filter(pk=adas_goal.pk).exists()
    assert Goal.objects.filter(pk=graces_goal.pk).exists()


def test_goal_status_has_three_labelled_choices():
    assert Goal.Status.choices == [
        ("planned", "Planned"),
        ("in_progress", "In progress"),
        ("done", "Done"),
    ]


@pytest.mark.django_db
def test_new_goal_starts_as_planned_and_displays_status_label(user):
    goal = Goal.objects.create(user=user, title="Learn Django")

    assert goal.status == "planned"
    goal.status = Goal.Status.IN_PROGRESS
    assert goal.get_status_display() == "In progress"


@pytest.mark.django_db
def test_full_clean_rejects_an_unknown_status(user):
    goal = Goal(user=user, title="Learn Django", description=DESCRIPTION, status="archived")

    with pytest.raises(ValidationError) as excinfo:
        goal.full_clean()

    assert set(excinfo.value.error_dict) == {"status"}
    assert [error.code for error in excinfo.value.error_dict["status"]] == ["invalid_choice"]


@pytest.mark.django_db
def test_full_clean_requires_a_description(user):
    goal = Goal(user=user, title="Learn Django", description="")

    with pytest.raises(ValidationError) as excinfo:
        goal.full_clean()

    assert set(excinfo.value.error_dict) == {"description"}
    goal.description = DESCRIPTION
    goal.full_clean()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("title", "valid"),
    [("", False), ("x" * 201, False), ("x" * 200, True)],
    ids=["empty", "201-characters", "200-characters"],
)
def test_full_clean_requires_a_title_of_at_most_200_characters(user, title, valid):
    goal = Goal(user=user, title=title, description=DESCRIPTION)

    if valid:
        goal.full_clean()
    else:
        with pytest.raises(ValidationError) as excinfo:
            goal.full_clean()
        assert set(excinfo.value.error_dict) == {"title"}
