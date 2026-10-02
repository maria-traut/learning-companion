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


@pytest.mark.django_db
def test_admin_goal_list_can_be_filtered_by_status(admin_client, user):
    for title, status in (("Plan", "planned"), ("Doing", "in_progress"), ("Done", "done")):
        Goal.objects.create(user=user, title=title, description=DESCRIPTION, status=status)
    done_goals = list(Goal.objects.filter(status="done"))

    page = admin_client.get("/admin/goals/goal/").content.decode()
    by_status = admin_client.get("/admin/goals/goal/", {"status": "done"})
    by_filter_link = admin_client.get("/admin/goals/goal/", {"status__exact": "done"})

    sidebar = re.search(r'<search id="changelist-filter"[^>]*>(.*?)</search>', page, re.DOTALL)
    assert sidebar
    assert re.search(r"By status", sidebar.group(1))
    for label in ("Planned", "In progress", "Done"):
        assert re.search(rf">\s*{label}\s*</a>", sidebar.group(1)), label
    assert list(by_status.context["cl"].result_list) == done_goals
    assert list(by_filter_link.context["cl"].result_list) == done_goals


@pytest.mark.django_db
def test_admin_goal_list_can_be_searched_by_title(admin_client, user):
    django_goal = Goal.objects.create(user=user, title="Learn Django", description=DESCRIPTION)
    orm_goal = Goal.objects.create(user=user, title="Django ORM deep dive", description=DESCRIPTION)
    Goal.objects.create(user=user, title="Learn SQL", description=DESCRIPTION)

    response = admin_client.get("/admin/goals/goal/", {"q": "django"})

    assert set(response.context["cl"].result_list) == {django_goal, orm_goal}


@pytest.mark.django_db
def test_superuser_can_add_a_goal_for_a_chosen_owner(admin_client, user):
    page = admin_client.get("/admin/goals/goal/add/").content.decode()

    response = admin_client.post(
        "/admin/goals/goal/add/",
        {
            "user": user.pk,
            "title": "Learn Django",
            "description": DESCRIPTION,
            "status": "in_progress",
        },
    )

    assert re.search(r'<select[^>]*name="user"', page)
    assert response.status_code == 302
    assert response.url == "/admin/goals/goal/"
    goal = Goal.objects.get()
    assert goal.user == user
    assert (goal.title, goal.description, goal.status) == (
        "Learn Django",
        DESCRIPTION,
        "in_progress",
    )


@pytest.mark.django_db
def test_crafted_post_cannot_change_a_goals_owner(admin_client, django_user_model, user):
    grace = django_user_model.objects.create_user(username="grace", password=PASSWORD)
    goal = Goal.objects.create(user=user, title="Learn Django", description=DESCRIPTION)
    url = f"/admin/goals/goal/{goal.pk}/change/"

    page = admin_client.get(url).content.decode()
    response = admin_client.post(
        url,
        {
            "user": grace.pk,
            "title": "Learn Django properly",
            "description": "Build a small project.",
            "status": "done",
        },
    )

    assert not re.search(r'name="user"', page)
    assert response.status_code == 302
    stored = Goal.objects.get(pk=goal.pk)
    assert stored.user == user
    assert (stored.title, stored.description, stored.status) == (
        "Learn Django properly",
        "Build a small project.",
        "done",
    )


@pytest.mark.django_db
def test_goal_timestamps_are_shown_read_only_in_the_admin(admin_client, user):
    goal = Goal.objects.create(user=user, title="Learn Django", description=DESCRIPTION)

    change_page = admin_client.get(f"/admin/goals/goal/{goal.pk}/change/").content.decode()
    add_page = admin_client.get("/admin/goals/goal/add/").content.decode()

    for field in ("created_at", "updated_at"):
        assert re.search(
            rf'class="[^"]*\bfield-{field}\b[^"]*">.*?<div class="readonly">',
            change_page,
            re.DOTALL,
        ), field
        assert not re.search(rf'name="{field}"', change_page)
        assert not re.search(rf'name="{field}"', add_page)
