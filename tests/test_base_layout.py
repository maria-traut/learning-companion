import re

from django.template.loader import render_to_string


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
