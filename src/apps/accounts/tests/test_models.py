import pytest
from django.db import IntegrityError

from apps.accounts.models import FocusArea

PASSWORD = "correct-horse-battery-9"


def test_focus_area_displays_as_its_name():
    focus_area = FocusArea(name="django")

    assert str(focus_area) == "django"


@pytest.mark.django_db
def test_focus_area_names_are_unique():
    FocusArea.objects.create(name="django")

    with pytest.raises(IntegrityError):
        FocusArea.objects.create(name="django")


@pytest.mark.django_db
def test_create_user_gives_the_user_one_empty_profile(django_user_model):
    user = django_user_model.objects.create_user(username="ada", password=PASSWORD)

    assert hasattr(user, "profile")
    assert type(user.profile).objects.filter(user=user).count() == 1
    assert user.profile.name == ""
    assert user.profile.cohort == ""
    assert not user.profile.focus_areas.exists()
