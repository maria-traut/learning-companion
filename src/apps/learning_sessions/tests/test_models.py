from datetime import UTC, date, datetime, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.goals.models import Goal
from apps.learning_sessions.models import LearningSession, Tag

PASSWORD = "correct-horse-battery-9"
DESCRIPTION = "Work through the official tutorial."


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="ada", password=PASSWORD)


@pytest.fixture
def goal(user):
    return Goal.objects.create(user=user, title="Learn Django", description=DESCRIPTION)


def test_tag_displays_as_its_name():
    tag = Tag(name="django")

    assert str(tag) == "django"


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("name", "valid"),
    [("", False), ("x" * 51, False), ("x" * 50, True)],
    ids=["empty", "51-chars", "50-chars"],
)
def test_full_clean_requires_a_tag_name_of_at_most_50_characters(name, valid):
    tag = Tag(name=name)

    if valid:
        tag.full_clean()
    else:
        with pytest.raises(ValidationError) as excinfo:
            tag.full_clean()
        assert set(excinfo.value.error_dict) == {"name"}


@pytest.mark.django_db
def test_full_clean_rejects_a_duplicate_tag_name():
    Tag.objects.create(name="django")

    with pytest.raises(ValidationError) as excinfo:
        Tag(name="django").full_clean()

    assert set(excinfo.value.error_dict) == {"name"}
    assert [e.code for e in excinfo.value.error_dict["name"]] == ["unique"]


@pytest.mark.django_db
def test_tags_are_listed_by_name():
    orm = Tag.objects.create(name="orm")
    django = Tag.objects.create(name="django")
    python = Tag.objects.create(name="python")

    assert list(Tag.objects.all()) == [django, orm, python]


def test_session_displays_as_goal_title_date_and_duration():
    session = LearningSession(
        goal=Goal(title="Learn Django"), date=date(2026, 9, 7), duration_minutes=45
    )

    assert str(session) == "Learn Django – 2026-09-07 (45 min)"


@pytest.mark.django_db
def test_goal_sessions_contains_exactly_that_goals_sessions(user, goal):
    other_goal = Goal.objects.create(user=user, title="Learn SQL", description=DESCRIPTION)
    first = LearningSession.objects.create(goal=goal, date=date(2026, 9, 1), duration_minutes=30)
    second = LearningSession.objects.create(goal=goal, date=date(2026, 9, 2), duration_minutes=60)
    LearningSession.objects.create(goal=other_goal, date=date(2026, 9, 3), duration_minutes=15)

    assert set(goal.sessions.all()) == {first, second}


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("duration_minutes", "valid"),
    [(0, False), (-5, False), (1, True)],
    ids=["zero", "negative", "one-minute"],
)
def test_full_clean_requires_a_duration_of_at_least_one_minute(goal, duration_minutes, valid):
    session = LearningSession(goal=goal, date=date(2026, 9, 1), duration_minutes=duration_minutes)

    if valid:
        session.full_clean()
    else:
        with pytest.raises(ValidationError) as excinfo:
            session.full_clean()
        assert set(excinfo.value.error_dict) == {"duration_minutes"}


def test_full_clean_requires_a_goal_and_a_date():
    session = LearningSession(date=None, duration_minutes=30)

    with pytest.raises(ValidationError) as excinfo:
        session.full_clean()

    assert set(excinfo.value.error_dict) == {"goal", "date"}


@pytest.mark.django_db
def test_full_clean_accepts_empty_notes(goal):
    session = LearningSession(goal=goal, date=date(2026, 9, 1), duration_minutes=30, notes="")

    session.full_clean()


@pytest.mark.django_db
def test_session_date_defaults_to_today(goal):
    session = LearningSession.objects.create(goal=goal, duration_minutes=30)

    assert session.date == timezone.localdate()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("days_from_today", "valid"),
    [(1, False), (0, True), (-30, True)],
    ids=["tomorrow", "today", "a-month-ago"],
)
def test_full_clean_rejects_a_session_date_after_today(goal, days_from_today, valid):
    session_date = timezone.localdate() + timedelta(days=days_from_today)
    session = LearningSession(goal=goal, date=session_date, duration_minutes=30)

    if valid:
        session.full_clean()
    else:
        with pytest.raises(ValidationError) as excinfo:
            session.full_clean()
        assert set(excinfo.value.error_dict) == {"date"}


@pytest.mark.django_db
def test_sessions_and_tags_are_many_to_many(goal):
    django = Tag.objects.create(name="django")
    orm = Tag.objects.create(name="orm")
    first = LearningSession.objects.create(goal=goal, date=date(2026, 9, 1), duration_minutes=30)
    second = LearningSession.objects.create(goal=goal, date=date(2026, 9, 2), duration_minutes=60)

    first.tags.add(django, orm)
    second.tags.add(django)

    assert set(first.tags.all()) == {django, orm}
    assert set(django.sessions.all()) == {first, second}
    assert set(orm.sessions.all()) == {first}


@pytest.mark.django_db
def test_sessions_are_listed_newest_date_first_then_newest_created_first(goal):
    older_day = LearningSession.objects.create(
        goal=goal, date=date(2026, 9, 2), duration_minutes=30
    )
    newer_day = LearningSession.objects.create(
        goal=goal, date=date(2026, 9, 3), duration_minutes=30
    )
    same_day_early = LearningSession.objects.create(
        goal=goal, date=date(2026, 9, 2), duration_minutes=30
    )
    same_day_late = LearningSession.objects.create(
        goal=goal, date=date(2026, 9, 2), duration_minutes=30
    )
    for session, hour in ((older_day, 12), (same_day_early, 9), (same_day_late, 18)):
        LearningSession.objects.filter(pk=session.pk).update(
            created_at=datetime(2026, 9, 2, hour, tzinfo=UTC)
        )

    assert list(LearningSession.objects.all()) == [
        newer_day,
        same_day_late,
        older_day,
        same_day_early,
    ]
