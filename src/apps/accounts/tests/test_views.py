import re


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
