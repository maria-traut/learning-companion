import re

import pytest

from apps.accounts.models import FocusArea

PASSWORD = "correct-horse-battery-9"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url",
    [
        "/admin/accounts/profile/",
        "/admin/accounts/profile/add/",
        "/admin/accounts/focusarea/",
        "/admin/accounts/focusarea/add/",
    ],
    ids=["profile-list", "profile-add", "focusarea-list", "focusarea-add"],
)
def test_admin_pages_for_profiles_and_focus_areas_load_for_a_superuser(admin_client, url):
    response = admin_client.get(url)

    assert response.status_code == 200


@pytest.mark.django_db
def test_superuser_can_edit_name_cohort_and_focus_areas_of_a_profile(
    admin_client, django_user_model
):
    ada = django_user_model.objects.create_user(username="ada", password=PASSWORD)
    django = FocusArea.objects.create(name="django")
    sql = FocusArea.objects.create(name="sql")
    url = f"/admin/accounts/profile/{ada.profile.pk}/change/"

    page = admin_client.get(url).content.decode()
    response = admin_client.post(
        url,
        {
            "user": ada.pk,
            "name": "Ada Lovelace",
            "cohort": "Web Dev Berlin 2026-03",
            "focus_areas": [django.pk, sql.pk],
        },
    )

    for field in ("name", "cohort", "focus_areas"):
        assert re.search(rf'name="{field}"', page)
    assert response.status_code == 302
    ada.profile.refresh_from_db()
    assert ada.profile.name == "Ada Lovelace"
    assert ada.profile.cohort == "Web Dev Berlin 2026-03"
    assert list(ada.profile.focus_areas.all()) == [django, sql]


@pytest.mark.django_db
def test_superuser_can_save_a_profile_with_name_cohort_and_focus_areas_left_empty(
    admin_client, django_user_model
):
    ada = django_user_model.objects.create_user(username="ada", password=PASSWORD)
    ada.profile.name = "Ada Lovelace"
    ada.profile.cohort = "Web Dev Berlin 2026-03"
    ada.profile.save()
    ada.profile.focus_areas.add(FocusArea.objects.create(name="django"))

    response = admin_client.post(
        f"/admin/accounts/profile/{ada.profile.pk}/change/",
        {"user": ada.pk, "name": "", "cohort": ""},
    )

    assert response.status_code == 302
    ada.profile.refresh_from_db()
    assert ada.profile.name == ""
    assert ada.profile.cohort == ""
    assert not ada.profile.focus_areas.exists()
