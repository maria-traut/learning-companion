import re

import pytest
from django.conf import settings
from django.shortcuts import resolve_url
from django.urls import reverse

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


def signup_data(username="ada", password1=PASSWORD, password2=PASSWORD):
    return {"username": username, "password1": password1, "password2": password2}


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
