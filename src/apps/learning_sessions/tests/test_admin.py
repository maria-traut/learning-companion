import re
from datetime import date

import pytest

from apps.goals.models import Goal
from apps.learning_sessions.models import LearningSession, Tag

PASSWORD = "correct-horse-battery-9"
DESCRIPTION = "Work through the official tutorial."
SESSION_LIST = "/admin/learning_sessions/learningsession/"
SESSION_ADD = "/admin/learning_sessions/learningsession/add/"
TAG_LIST = "/admin/learning_sessions/tag/"


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


@pytest.mark.django_db
def test_admin_session_list_can_be_filtered_by_date_and_tags(admin_client, goal):
    django = Tag.objects.create(name="django")
    orm = Tag.objects.create(name="orm")
    tagged = LearningSession.objects.create(goal=goal, date=date(2026, 9, 1), duration_minutes=30)
    tagged.tags.add(django)
    other = LearningSession.objects.create(goal=goal, date=date(2026, 9, 2), duration_minutes=30)
    other.tags.add(orm)

    page = admin_client.get(SESSION_LIST).content.decode()
    by_tag = admin_client.get(SESSION_LIST, {"tags__id__exact": django.pk})

    sidebar = re.search(r'<search id="changelist-filter"[^>]*>(.*?)</search>', page, re.DOTALL)
    assert sidebar
    assert re.search(r"By date", sidebar.group(1))
    assert re.search(r"By tags", sidebar.group(1))
    for label in ("django", "orm"):
        assert re.search(rf">\s*{label}\s*</a>", sidebar.group(1)), label
    assert list(by_tag.context["cl"].result_list) == [tagged]


@pytest.mark.django_db
def test_admin_session_list_can_be_searched_by_notes_and_goal_title(admin_client, user, goal):
    sql_goal = Goal.objects.create(user=user, title="Learn SQL", description=DESCRIPTION)
    by_notes = LearningSession.objects.create(
        goal=sql_goal, date=date(2026, 9, 1), duration_minutes=30, notes="Read the Django ORM docs"
    )
    by_goal_title = LearningSession.objects.create(
        goal=goal, date=date(2026, 9, 2), duration_minutes=30, notes="Tutorial part 2"
    )
    LearningSession.objects.create(
        goal=sql_goal, date=date(2026, 9, 3), duration_minutes=30, notes="Joins"
    )

    response = admin_client.get(SESSION_LIST, {"q": "django"})

    assert set(response.context["cl"].result_list) == {by_notes, by_goal_title}


@pytest.mark.django_db
def test_admin_tag_list_can_be_searched_by_name(admin_client):
    django = Tag.objects.create(name="django")
    django_orm = Tag.objects.create(name="django-orm")
    Tag.objects.create(name="sql")

    response = admin_client.get(TAG_LIST, {"q": "django"})

    assert response.status_code == 200
    assert set(response.context["cl"].result_list) == {django, django_orm}


@pytest.mark.django_db
def test_admin_add_session_requires_at_least_one_tag(admin_client, goal):
    django = Tag.objects.create(name="django")
    data = {"goal": goal.pk, "date": "2026-09-01", "duration_minutes": 45, "notes": ""}

    without_tags = admin_client.post(SESSION_ADD, data)

    assert without_tags.status_code == 200
    assert "tags" in without_tags.context["adminform"].form.errors
    assert not LearningSession.objects.exists()

    with_tag = admin_client.post(SESSION_ADD, {**data, "tags": [django.pk]})

    assert with_tag.status_code == 302
    session = LearningSession.objects.get()
    assert set(session.tags.all()) == {django}
