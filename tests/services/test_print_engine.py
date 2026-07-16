"""Print engine unit tests (no printer / PDF device required)."""

from __future__ import annotations

from magiceditor.services.print_engine import printable_css


def test_printable_css_is_light() -> None:
    css = printable_css()
    assert "#ffffff" in css
    assert "#000000" in css
    assert "Cascadia Code" in css
