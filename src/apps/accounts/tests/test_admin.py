import re

import pytest

from apps.accounts.models import FocusArea, Profile

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
    django_area = FocusArea.objects.create(name="django")
    sql_area = FocusArea.objects.create(name="sql")
    url = f"/admin/accounts/profile/{ada.profile.pk}/change/"

    page = admin_client.get(url).content.decode()
    response = admin_client.post(
        url,
        {
            "name": "Ada Lovelace",
            "cohort": "Web Dev Berlin 2026-03",
            "focus_areas": [django_area.pk, sql_area.pk],
        },
    )

    for field in ("name", "cohort", "focus_areas"):
        assert re.search(rf'name="{field}"', page)
    assert response.status_code == 302
    ada.profile.refresh_from_db()
    assert ada.profile.name == "Ada Lovelace"
    assert ada.profile.cohort == "Web Dev Berlin 2026-03"
    assert list(ada.profile.focus_areas.all()) == [django_area, sql_area]


@pytest.mark.django_db
def test_profile_user_is_read_only_on_the_admin_change_page(admin_client, django_user_model):
    ada = django_user_model.objects.create_user(username="ada", password=PASSWORD)
    bob = django_user_model.objects.create_user(username="bob", password=PASSWORD)
    bob.profile.delete()
    url = f"/admin/accounts/profile/{ada.profile.pk}/change/"

    page = admin_client.get(url).content.decode()
    response = admin_client.post(url, {"user": bob.pk, "name": "Ada Lovelace", "cohort": ""})

    assert not re.search(r'name="user"', page)
    assert response.status_code == 302
    profile = Profile.objects.get(pk=ada.profile.pk)
    assert profile.user == ada
    assert profile.name == "Ada Lovelace"
    assert not Profile.objects.filter(user=bob).exists()


def test_profile_user_is_selectable_on_the_admin_add_page(admin_client):
    page = admin_client.get("/admin/accounts/profile/add/").content.decode()

    assert re.search(r'<select[^>]*name="user"', page)


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
        {"name": "", "cohort": ""},
    )

    assert response.status_code == 302
    ada.profile.refresh_from_db()
    assert ada.profile.name == ""
    assert ada.profile.cohort == ""
    assert not ada.profile.focus_areas.exists()
