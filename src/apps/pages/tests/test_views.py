import re


def test_home_page_is_served_to_anonymous_visitors(client):
    response = client.get("/")

    assert response.status_code == 200


def test_home_page_extends_base_layout(client):
    response = client.get("/")

    template_names = [template.name for template in response.templates]
    assert "pages/home.html" in template_names
    assert "base.html" in template_names


def test_home_page_title(client):
    response = client.get("/")

    assert "<title>Home · Learning Companion</title>" in response.content.decode()


def test_home_page_shows_welcome_heading_and_text(client):
    response = client.get("/")

    html = response.content.decode()
    assert re.search(r"<h1>.+</h1>", html)
    for topic in ("goals", "sessions", "resources", "AI summaries"):
        assert topic in html
