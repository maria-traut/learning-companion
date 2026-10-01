import re

import pytest
from django.contrib import messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.template.loader import render_to_string


def request_with_messages(rf):
    request = rf.get("/")
    SessionMiddleware(lambda request: None).process_request(request)
    MessageMiddleware(lambda request: None).process_request(request)
    return request


def test_base_layout_links_pinned_pico_css_from_cdn():
    html = render_to_string("base.html")

    assert re.search(
        r'<link rel="stylesheet" href="https://cdn\.jsdelivr\.net/npm/@picocss/pico@\d+\.\d+\.\d+/'
        r'css/pico\.min\.css">',
        html,
    )


def test_base_layout_nav_links_app_name_to_home():
    html = render_to_string("base.html")

    nav = re.search(r"<nav>(.*?)</nav>", html, re.DOTALL)
    assert nav
    assert re.search(r'<a href="/"[^>]*>\s*Learning Companion\s*</a>', nav.group(1))


def test_base_layout_has_default_title():
    html = render_to_string("base.html")

    assert "<title>Learning Companion</title>" in html


@pytest.mark.django_db
def test_base_layout_renders_messages(rf):
    request = request_with_messages(rf)
    messages.success(request, "Goal saved.")

    html = render_to_string("base.html", request=request)

    container = re.search(r'<section id="messages"[^>]*>(.*?)</section>', html, re.DOTALL)
    assert container
    assert "Goal saved." in container.group(1)


@pytest.mark.django_db
def test_base_layout_omits_messages_container_without_messages(rf):
    request = request_with_messages(rf)

    html = render_to_string("base.html", request=request)

    assert 'id="messages"' not in html
