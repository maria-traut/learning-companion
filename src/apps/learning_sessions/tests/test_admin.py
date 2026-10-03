import re
from datetime import date

import pytest

from apps.goals.models import Goal
from apps.learning_sessions.models import LearningSession

PASSWORD = "correct-horse-battery-9"
DESCRIPTION = "Work through the official tutorial."
SESSION_LIST = "/admin/learning_sessions/learningsession/"


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="ada", password=PASSWORD)


@pytest.fixture
def goal(user):
    return Goal.objects.create(user=user, title="Learn Django", description=DESCRIPTION)


@pytest.mark.django_db
def test_admin_session_list_shows_goal_date_and_duration(admin_client, goal):
    LearningSession.objects.create(goal=goal, date=date(2026, 9, 1), duration_minutes=30)

    response = admin_client.get(SESSION_LIST)

    assert response.status_code == 200
    page = response.content.decode()
    for field in ("goal", "date", "duration_minutes"):
        assert re.search(rf'<th scope="col"[^>]*class="[^"]*\bcolumn-{field}\b', page), field
