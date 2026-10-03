from apps.learning_sessions.models import Tag


def test_tag_displays_as_its_name():
    tag = Tag(name="django")

    assert str(tag) == "django"
