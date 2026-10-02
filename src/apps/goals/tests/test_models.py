from apps.goals.models import Goal


def test_goal_displays_as_its_title():
    goal = Goal(title="Learn Django")

    assert str(goal) == "Learn Django"
