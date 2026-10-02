import pytest
from django.db import IntegrityError

from apps.accounts.models import FocusArea


def test_focus_area_displays_as_its_name():
    focus_area = FocusArea(name="django")

    assert str(focus_area) == "django"


@pytest.mark.django_db
def test_focus_area_names_are_unique():
    FocusArea.objects.create(name="django")

    with pytest.raises(IntegrityError):
        FocusArea.objects.create(name="django")
