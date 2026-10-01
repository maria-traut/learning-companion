import re

from django.template.loader import render_to_string


def test_base_layout_links_pinned_pico_css_from_cdn():
    html = render_to_string("base.html")

    assert re.search(
        r'<link rel="stylesheet" href="https://cdn\.jsdelivr\.net/npm/@picocss/pico@\d+\.\d+\.\d+/'
        r'css/pico\.min\.css">',
        html,
    )
