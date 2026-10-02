from apps.accounts.models import FocusArea


def test_focus_area_displays_as_its_name():
    focus_area = FocusArea(name="django")

    assert str(focus_area) == "django"
