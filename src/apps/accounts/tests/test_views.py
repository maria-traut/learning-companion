import re

import pytest
from django.conf import settings
from django.shortcuts import resolve_url
from django.urls import reverse

from apps.accounts.models import FocusArea, Profile

PASSWORD = "correct-horse-battery-9"


def template_names(response):
    return [template.name for template in response.templates]


def messages_text(response):
    container = re.search(
        r'<section id="messages"[^>]*>(.*?)</section>', response.content.decode(), re.DOTALL
    )
    return container.group(1) if container else ""


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="ada", password=PASSWORD)


def nav_html(response):
    nav = re.search(r"<nav[^>]*>(.*?)</nav>", response.content.decode(), re.DOTALL)
    assert nav
    return nav.group(1)


def signup_data(username="ada", password1=PASSWORD, password2=PASSWORD):
    return {"username": username, "password1": password1, "password2": password2}


def main_html(response):
    main = re.search(r"<main[^>]*>(.*?)</main>", response.content.decode(), re.DOTALL)
    assert main
    return main.group(1)


def profile_values(response):
    dl = re.search(r"<dl>(.*?)</dl>", response.content.decode(), re.DOTALL)
    assert dl
    return [
        value.strip()
        for value in re.findall(r"<(?:dd|li)>([^<]*)</(?:dd|li)>", dl.group(1))
        if value.strip()
    ]


def form_field_names(response):
    form = re.search(r'<form method="post">(.*?)</form>', response.content.decode(), re.DOTALL)
    assert form
    names = set(re.findall(r'<(?:input|select|textarea)[^>]*name="([^"]+)"', form.group(1)))
    return names - {"csrfmiddlewaretoken"}


def focus_area_checkboxes(html):
    tags = re.findall(r'<input type="checkbox" name="focus_areas" value="(\d+)"([^>]*)>', html)
    return {int(pk): "checked" in attrs for pk, attrs in tags}


def fill_profile(user, name, cohort, focus_area_names):
    user.profile.name = name
    user.profile.cohort = cohort
    user.profile.save()
    user.profile.focus_areas.set(
        FocusArea.objects.get_or_create(name=area)[0] for area in focus_area_names
    )


def test_signup_page_is_served_to_anonymous_visitors(client):
    response = client.get("/accounts/signup/")

    assert response.status_code == 200
    assert "registration/signup.html" in template_names(response)
    assert "base.html" in template_names(response)
    html = response.content.decode()
    for field in ("username", "password1", "password2"):
        assert re.search(rf'<input[^>]*name="{field}"', html)


def test_login_page_is_served_to_anonymous_visitors(client):
    response = client.get("/accounts/login/")

    assert response.status_code == 200
    assert "registration/login.html" in template_names(response)
    assert "base.html" in template_names(response)
    html = response.content.decode()
    for field in ("username", "password"):
        assert re.search(rf'<input[^>]*name="{field}"', html)


def test_login_url_setting_points_at_login_page():
    assert resolve_url(settings.LOGIN_URL) == reverse("accounts:login")


@pytest.mark.django_db
def test_valid_signup_creates_user_and_redirects_to_login_without_logging_in(
    client, django_user_model
):
    response = client.post("/accounts/signup/", signup_data())

    assert response.status_code == 302
    assert response.url == "/accounts/login/"
    assert django_user_model.objects.filter(username="ada").exists()
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_signup_shows_account_created_message_on_login_page(client):
    response = client.post("/accounts/signup/", signup_data(), follow=True)

    assert response.redirect_chain == [("/accounts/login/", 302)]
    assert "Account created" in messages_text(response)


@pytest.mark.django_db
def test_valid_signup_creates_one_empty_profile_for_the_new_user(client, django_user_model):
    client.post("/accounts/signup/", signup_data())

    user = django_user_model.objects.get(username="ada")
    assert Profile.objects.filter(user=user).count() == 1
    assert user.profile.name == ""
    assert user.profile.cohort == ""
    assert not user.profile.focus_areas.exists()


def test_signup_form_asks_only_for_username_and_passwords(client):
    response = client.get("/accounts/signup/")

    assert form_field_names(response) == {"username", "password1", "password2"}


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("data", "error"),
    [
        (signup_data(username="grace", password2="something-else-entirely-7"), "didn’t match"),
        (signup_data(username="ADA"), "A user with that username already exists."),
        (signup_data(username="grace", password1="12345678", password2="12345678"), "too common"),
    ],
    ids=["mismatched-passwords", "username-taken", "weak-password"],
)
def test_invalid_signup_rerenders_form_with_error_and_creates_no_user(
    client, django_user_model, data, error
):
    django_user_model.objects.create_user(username="ada", password=PASSWORD)

    response = client.post("/accounts/signup/", data)

    assert response.status_code == 200
    assert "registration/signup.html" in template_names(response)
    assert error in response.content.decode()
    assert django_user_model.objects.count() == 1


@pytest.mark.django_db
def test_valid_login_redirects_home_and_authenticates(client, user):
    response = client.post("/accounts/login/", {"username": "ada", "password": PASSWORD})

    assert response.status_code == 302
    assert response.url == "/"
    assert client.session["_auth_user_id"] == str(user.pk)


@pytest.mark.django_db
def test_login_shows_welcome_message(client, user):
    response = client.post(
        "/accounts/login/", {"username": "ada", "password": PASSWORD}, follow=True
    )

    assert response.redirect_chain == [("/", 302)]
    assert "Welcome, ada" in messages_text(response)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("next_url", "expected_redirect"),
    [
        ("/some/safe/path/", "/some/safe/path/"),
        ("https://evil.example.com/", "/"),
    ],
    ids=["same-site", "external"],
)
def test_login_follows_only_safe_next_url(client, user, next_url, expected_redirect):
    response = client.post(
        f"/accounts/login/?next={next_url}", {"username": "ada", "password": PASSWORD}
    )

    assert response.status_code == 302
    assert response.url == expected_redirect


@pytest.mark.django_db
def test_login_with_wrong_password_shows_error_and_stays_anonymous(client, user):
    response = client.post("/accounts/login/", {"username": "ada", "password": "wrong-password"})

    assert response.status_code == 200
    assert "registration/login.html" in template_names(response)
    assert "Please enter a correct username and password" in response.content.decode()
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_logout_via_post_logs_out_and_redirects_home(client, user):
    client.force_login(user)

    response = client.post("/accounts/logout/")

    assert response.status_code == 302
    assert response.url == "/"
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_logout_shows_logged_out_message_on_home_page(client, user):
    client.force_login(user)

    response = client.post("/accounts/logout/", follow=True)

    assert response.redirect_chain == [("/", 302)]
    assert "You have been logged out" in messages_text(response)


@pytest.mark.django_db
def test_logout_via_get_is_not_allowed_and_keeps_user_logged_in(client, user):
    client.force_login(user)

    response = client.get("/accounts/logout/")

    assert response.status_code == 405
    assert client.session["_auth_user_id"] == str(user.pk)


def test_nav_offers_login_and_signup_to_anonymous_visitors(client):
    nav = nav_html(client.get("/"))

    assert re.search(r'<a href="/accounts/login/"[^>]*>\s*Log in\s*</a>', nav)
    assert re.search(r'<a href="/accounts/signup/"[^>]*>\s*Sign up\s*</a>', nav)
    assert "/accounts/logout/" not in nav


@pytest.mark.django_db
def test_nav_shows_username_and_logout_form_to_logged_in_users(client, user):
    client.force_login(user)

    nav = nav_html(client.get("/"))

    assert "ada" in nav
    logout_form = re.search(
        r'<form method="post" action="/accounts/logout/"[^>]*>(.*?)</form>', nav, re.DOTALL
    )
    assert logout_form
    assert 'name="csrfmiddlewaretoken"' in logout_form.group(1)
    assert re.search(r"<button[^>]*>\s*Log out\s*</button>", logout_form.group(1))
    assert "/accounts/login/" not in nav
    assert "/accounts/signup/" not in nav


@pytest.mark.django_db
def test_nav_username_links_logged_in_users_to_their_profile(client, user):
    client.force_login(user)

    nav = nav_html(client.get("/"))

    assert re.search(r'<a href="/accounts/profile/"[^>]*>\s*ada\s*</a>', nav)


def test_nav_has_no_profile_link_for_anonymous_visitors(client):
    nav = nav_html(client.get("/"))

    assert "/accounts/profile/" not in nav


@pytest.mark.django_db
def test_logged_in_user_is_redirected_home_from_login_page(client, user):
    client.force_login(user)

    response = client.get("/accounts/login/")

    assert response.status_code == 302
    assert response.url == "/"


@pytest.mark.django_db
def test_logged_in_user_is_redirected_home_from_signup_page(client, user):
    client.force_login(user)

    response = client.get("/accounts/signup/")

    assert response.status_code == 302
    assert response.url == "/"


def test_profile_page_redirects_anonymous_visitors_to_login(client):
    response = client.get("/accounts/profile/")

    assert response.status_code == 302
    assert response.url == "/accounts/login/?next=/accounts/profile/"


@pytest.mark.django_db
def test_profile_page_shows_the_users_own_details(client, user):
    fill_profile(user, "Ada Lovelace", "Web Dev Berlin 2026-03", ["django", "sql"])
    client.force_login(user)

    response = client.get("/accounts/profile/")

    assert response.status_code == 200
    assert "accounts/profile_detail.html" in template_names(response)
    assert "base.html" in template_names(response)
    assert profile_values(response) == [
        "ada",
        "Ada Lovelace",
        "Web Dev Berlin 2026-03",
        "django",
        "sql",
    ]


@pytest.mark.django_db
def test_empty_profile_page_shows_placeholders(client, user):
    client.force_login(user)

    response = client.get("/accounts/profile/")

    assert profile_values(response) == ["ada", "Not set yet", "Not set yet", "No focus areas yet"]


@pytest.mark.django_db
def test_profile_page_shows_only_the_logged_in_users_data(client, django_user_model, user):
    grace = django_user_model.objects.create_user(username="grace", password=PASSWORD)
    fill_profile(user, "Ada Lovelace", "Berlin 2026-03", ["django"])
    fill_profile(grace, "Grace Hopper", "Hamburg 2025-09", ["cobol"])

    client.force_login(user)
    adas_page = client.get("/accounts/profile/")
    client.force_login(grace)
    graces_page = client.get("/accounts/profile/")

    assert profile_values(adas_page) == ["ada", "Ada Lovelace", "Berlin 2026-03", "django"]
    assert profile_values(graces_page) == ["grace", "Grace Hopper", "Hamburg 2025-09", "cobol"]
    assert "Grace Hopper" not in main_html(adas_page)
    assert "Hamburg 2025-09" not in main_html(adas_page)
    assert "Ada Lovelace" not in main_html(graces_page)
    assert "Berlin 2026-03" not in main_html(graces_page)


@pytest.mark.django_db
def test_profile_page_links_to_the_edit_page(client, user):
    client.force_login(user)

    response = client.get("/accounts/profile/")

    edit_link = r'<a href="/accounts/profile/edit/"[^>]*>\s*Edit profile\s*</a>'
    assert re.search(edit_link, main_html(response))


@pytest.mark.django_db
def test_profile_edit_form_is_prefilled_with_a_checkbox_per_focus_area(client, user):
    fill_profile(user, "Ada Lovelace", "Web Dev Berlin 2026-03", ["django", "sql"])
    testing = FocusArea.objects.create(name="testing")
    client.force_login(user)

    response = client.get("/accounts/profile/edit/")

    assert response.status_code == 200
    assert "accounts/profile_form.html" in template_names(response)
    html = response.content.decode()
    assert re.search(r'<input[^>]*name="name"[^>]*value="Ada Lovelace"', html)
    assert re.search(r'<input[^>]*name="cohort"[^>]*value="Web Dev Berlin 2026-03"', html)
    checkboxes = focus_area_checkboxes(html)
    assert set(checkboxes) == set(FocusArea.objects.values_list("pk", flat=True))
    checked = {pk for pk, is_checked in checkboxes.items() if is_checked}
    assert checked == set(user.profile.focus_areas.values_list("pk", flat=True))
    assert testing.pk not in checked


@pytest.mark.django_db
def test_profile_edit_form_has_exactly_name_cohort_and_focus_areas(client, user):
    FocusArea.objects.create(name="django")
    client.force_login(user)

    response = client.get("/accounts/profile/edit/")

    assert form_field_names(response) == {"name", "cohort", "focus_areas"}


@pytest.mark.django_db
def test_valid_profile_edit_saves_replaces_focus_areas_and_redirects(client, user):
    fill_profile(user, "Ada", "Berlin", ["django", "sql"])
    sql = FocusArea.objects.get(name="sql")
    testing = FocusArea.objects.create(name="testing")
    client.force_login(user)

    response = client.post(
        "/accounts/profile/edit/",
        {
            "name": "Ada Lovelace",
            "cohort": "Web Dev Berlin 2026-03",
            "focus_areas": [sql.pk, testing.pk],
        },
    )

    assert response.status_code == 302
    assert response.url == "/accounts/profile/"
    profile = Profile.objects.get(user=user)
    assert profile.name == "Ada Lovelace"
    assert profile.cohort == "Web Dev Berlin 2026-03"
    assert list(profile.focus_areas.all()) == [sql, testing]


@pytest.mark.django_db
def test_profile_edit_with_no_focus_areas_ticked_clears_them(client, user):
    fill_profile(user, "Ada", "Berlin", ["django", "sql"])
    client.force_login(user)

    response = client.post("/accounts/profile/edit/", {"name": "Ada", "cohort": "Berlin"})

    assert response.status_code == 302
    assert not Profile.objects.get(user=user).focus_areas.exists()


@pytest.mark.django_db
def test_profile_edit_shows_profile_updated_message_on_profile_page(client, user):
    client.force_login(user)

    response = client.post(
        "/accounts/profile/edit/", {"name": "Ada", "cohort": "Berlin"}, follow=True
    )

    assert response.redirect_chain == [("/accounts/profile/", 302)]
    assert "Profile updated" in messages_text(response)


@pytest.mark.django_db
def test_forged_owner_and_extra_fields_cannot_touch_another_profile(
    client, django_user_model, user
):
    grace = django_user_model.objects.create_user(username="grace", password=PASSWORD)
    fill_profile(grace, "Grace Hopper", "Hamburg 2025-09", ["cobol"])
    graces_profile = Profile.objects.get(user=grace)
    client.force_login(user)

    response = client.post(
        "/accounts/profile/edit/",
        {
            "name": "Ada Lovelace",
            "cohort": "Berlin",
            "user": grace.pk,
            "id": graces_profile.pk,
            "pk": graces_profile.pk,
        },
    )

    assert response.status_code == 302
    adas_profile = Profile.objects.get(name="Ada Lovelace")
    assert adas_profile.user == user
    assert Profile.objects.filter(user=user).count() == 1
    graces_profile.refresh_from_db()
    assert graces_profile.user == grace
    assert graces_profile.name == "Grace Hopper"
    assert graces_profile.cohort == "Hamburg 2025-09"
    assert [area.name for area in graces_profile.focus_areas.all()] == ["cobol"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("data", "error"),
    [
        ({"name": "x" * 101, "cohort": "Berlin"}, "at most 100 characters (it has 101)"),
        ({"name": "Ada", "cohort": "x" * 101}, "at most 100 characters (it has 101)"),
        (
            {"name": "Ada", "cohort": "Berlin", "focus_areas": [999]},
            "Select a valid choice. 999 is not one of the available choices.",
        ),
    ],
    ids=["name-too-long", "cohort-too-long", "unknown-focus-area"],
)
def test_invalid_profile_edit_rerenders_form_with_error_and_saves_nothing(
    client, user, data, error
):
    fill_profile(user, "Ada", "Berlin", ["django"])
    client.force_login(user)

    response = client.post("/accounts/profile/edit/", data)

    assert response.status_code == 200
    assert "accounts/profile_form.html" in template_names(response)
    assert error in response.content.decode()
    profile = Profile.objects.get(user=user)
    assert (profile.name, profile.cohort) == ("Ada", "Berlin")
    assert [area.name for area in profile.focus_areas.all()] == ["django"]


@pytest.mark.django_db
def test_profile_edit_without_focus_areas_says_so_and_still_saves(client, user):
    client.force_login(user)

    page = client.get("/accounts/profile/edit/")
    response = client.post("/accounts/profile/edit/", {"name": "Ada", "cohort": "Berlin"})

    assert "No focus areas available yet" in main_html(page)
    assert response.status_code == 302
    profile = Profile.objects.get(user=user)
    assert (profile.name, profile.cohort) == ("Ada", "Berlin")


@pytest.mark.django_db
def test_profile_edit_with_focus_areas_does_not_claim_there_are_none(client, user):
    FocusArea.objects.create(name="django")
    client.force_login(user)

    response = client.get("/accounts/profile/edit/")

    assert "No focus areas available yet" not in main_html(response)


@pytest.mark.django_db
@pytest.mark.parametrize("url", ["/accounts/profile/", "/accounts/profile/edit/"])
def test_profile_pages_create_a_missing_profile_on_the_spot(client, user, url):
    user.profile.delete()
    client.force_login(user)

    response = client.get(url)

    assert response.status_code == 200
    profile = Profile.objects.get(user=user)
    assert (profile.name, profile.cohort) == ("", "")
    assert not profile.focus_areas.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["get", "post"])
def test_profile_edit_page_redirects_anonymous_visitors_to_login(client, user, method):
    if method == "post":
        response = client.post("/accounts/profile/edit/", {"name": "Intruder"})
    else:
        response = client.get("/accounts/profile/edit/")

    assert response.status_code == 302
    assert response.url == "/accounts/login/?next=/accounts/profile/edit/"
    assert Profile.objects.get(user=user).name == ""
