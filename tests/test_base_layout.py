import re

import pytest
from django.contrib import messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import include, path


def add_message_and_redirect_home(request):
    messages.success(request, "Goal saved.")
    return redirect("pages:home")


urlpatterns = [
    path("add-message/", add_message_and_redirect_home),
    path("accounts/", include("apps.accounts.urls")),
    path("", include("apps.pages.urls")),
]


def request_with_messages(rf):
    request = rf.get("/")
    SessionMiddleware(lambda request: None).process_request(request)
    MessageMiddleware(lambda request: None).process_request(request)
    return request


PICO_HREF = re.compile(
    r'href="https://cdn\.jsdelivr\.net/npm/@picocss/pico@\d+\.\d+\.\d+/css/pico\.min\.css"'
)


def pico_link_tag(html):
    links = [tag for tag in re.findall(r"<link\b[^>]*>", html) if PICO_HREF.search(tag)]
    assert len(links) == 1
    return links[0]


def messages_container(html):
    container = re.search(r'<section id="messages"[^>]*>(.*?)</section>', html, re.DOTALL)
    assert container
    return container.group(1)


def test_base_layout_links_pinned_pico_css_from_cdn():
    html = render_to_string("base.html")

    assert 'rel="stylesheet"' in pico_link_tag(html)


def test_base_layout_pico_link_has_subresource_integrity():
    html = render_to_string("base.html")

    link = pico_link_tag(html)
    assert re.search(r'integrity="sha384-[A-Za-z0-9+/]{64}"', link)
    assert 'crossorigin="anonymous"' in link


def test_base_layout_nav_links_app_name_to_home():
    html = render_to_string("base.html")

    nav = re.search(r"<nav>(.*?)</nav>", html, re.DOTALL)
    assert nav
    assert re.search(r'<a href="/"[^>]*>\s*Learning Companion\s*</a>', nav.group(1))


def test_base_layout_has_default_title():
    html = render_to_string("base.html")

    assert "<title>Learning Companion</title>" in html


def test_base_layout_renders_messages(rf):
    request = request_with_messages(rf)
    messages.success(request, "Goal saved.")

    html = render_to_string("base.html", request=request)

    assert "Goal saved." in messages_container(html)


@pytest.mark.urls(__name__)
def test_message_added_in_one_request_appears_on_next_page(client):
    response = client.get("/add-message/", follow=True)

    assert response.redirect_chain == [("/", 302)]
    assert "Goal saved." in messages_container(response.content.decode())


def test_base_layout_renders_message_tags_as_css_classes(rf):
    request = request_with_messages(rf)
    messages.success(request, "Goal saved.")
    messages.info(request, "Heads up.", extra_tags="note")

    html = render_to_string("base.html", request=request)

    articles = re.findall(
        r'<article\b[^>]*\bclass="([^"]*)"[^>]*>\s*(.*?)\s*</article>',
        messages_container(html),
        re.DOTALL,
    )
    classes_by_text = {text: set(classes.split()) for classes, text in articles}
    assert classes_by_text == {"Goal saved.": {"success"}, "Heads up.": {"note", "info"}}


def test_base_layout_omits_messages_container_without_messages(rf):
    request = request_with_messages(rf)

    html = render_to_string("base.html", request=request)

    assert 'id="messages"' not in html


def test_base_layout_has_footer_with_app_name():
    html = render_to_string("base.html")

    footer = re.search(r"<footer[^>]*>(.*?)</footer>", html, re.DOTALL)
    assert footer
    assert "Learning Companion" in footer.group(1)
