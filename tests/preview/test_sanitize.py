"""Preview HTML sanitizer (L1-L3)."""

from magiceditor.preview.markdown_preview import render_markdown
from magiceditor.preview.sanitize import is_safe_href, sanitize_html


def test_sanitize_strips_script_and_handlers() -> None:
    html = '<p>ok</p><script>alert(1)</script><img src="https://x/y.png" onerror="x">'
    out = sanitize_html(html)
    assert "script" not in out.lower()
    assert "onerror" not in out.lower()
    assert "https://x/y.png" not in out


def test_sanitize_strips_style_body() -> None:
    out = sanitize_html("<style>color: red</style><p>Hi</p>")
    assert "color: red" not in out
    assert "<p>Hi</p>" in out
    unclosed = sanitize_html("<p>Hi</p><style>color: blue")
    assert "color: blue" not in unclosed
    assert "<p>Hi</p>" in unclosed


def test_sanitize_blocks_javascript_href() -> None:
    assert is_safe_href("javascript:alert(1)") is False
    assert is_safe_href("file:///etc/passwd") is False
    assert is_safe_href("https://example.com") is True
    assert is_safe_href("//evil.example/a") is False
    assert is_safe_href("javascript&#58;alert(1)") is False
    out = sanitize_html('<a href="javascript:alert(1)">x</a>')
    assert "javascript" not in out.lower()
    entity = sanitize_html('<a href="javascript&#58;alert(1)">x</a>')
    assert "javascript" not in entity.lower()
    assert "alert" not in entity.lower()


def test_attribute_quote_cannot_inject_markup() -> None:
    html = '<a href="https://example.com" title=\'foo" style="background:url(https://evil)\'>x</a>'
    out = sanitize_html(html)
    assert ' style="' not in out
    assert "https://example.com" in out
    assert out.lower().count("<a") == 1


def test_render_markdown_strips_raw_html_script() -> None:
    html = render_markdown("hello\n\n<script>alert(1)</script>")
    assert "script" not in html.lower()
    assert "hello" in html
