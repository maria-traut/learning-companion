import re

import pytest
from django.conf import settings
from django.shortcuts import resolve_url
from django.urls import reverse

PASSWORD = "correct-horse-battery-9"


def template_names(response):
    return [template.name for template in response.templates]


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
