from datetime import date

import pytest
from django.core.exceptions import ValidationError

from apps.goals.models import Goal
from apps.learning_sessions.models import LearningSession, Tag


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
