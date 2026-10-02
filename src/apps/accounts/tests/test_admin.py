import pytest


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
