import pytest
from django.db import IntegrityError
from django.db.models.signals import post_save

from apps.accounts.models import FocusArea, Profile

PASSWORD = "correct-horse-battery-9"


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="ada", password=PASSWORD)


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
    assert Profile.objects.filter(user=user).count() == 1
    assert user.profile.name == ""
    assert user.profile.cohort == ""
    assert not user.profile.focus_areas.exists()


@pytest.mark.django_db
def test_profile_displays_as_its_users_username(user):
    assert str(user.profile) == "ada"


@pytest.mark.django_db
def test_raw_save_as_in_loaddata_creates_no_profile(django_user_model, user):
    user.profile.delete()

    post_save.send(sender=django_user_model, instance=user, created=True, raw=True)

    assert not Profile.objects.filter(user=user).exists()
