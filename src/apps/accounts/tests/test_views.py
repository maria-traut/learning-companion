import re

from django.conf import settings
from django.shortcuts import resolve_url
from django.urls import reverse


def template_names(response):
    return [template.name for template in response.templates]


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
