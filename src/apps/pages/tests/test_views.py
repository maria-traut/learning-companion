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

    main = re.search(r"<main[^>]*>(.*?)</main>", response.content.decode(), re.DOTALL)
    assert main
    assert re.search(r"<h1>\s*\S.*?</h1>", main.group(1), re.DOTALL)
    for topic in ("goals", "sessions", "resources", "AI summaries", "next steps"):
        assert topic in main.group(1)
