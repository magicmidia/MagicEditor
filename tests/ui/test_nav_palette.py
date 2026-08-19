"""N8: autosave / theme bundle / split helpers used by the mixin."""

from magiceditor.ui.nav_palette import (
    autosave_interval_ms,
    parse_theme_bundle,
    split_view_text,
    theme_bundle_dict,
)


def test_autosave_interval_ms() -> None:
    assert autosave_interval_ms(0) == 0
    assert autosave_interval_ms(5) == 5000


def test_theme_bundle_roundtrip() -> None:
    payload = theme_bundle_dict("nord", "qlementine")
    assert parse_theme_bundle(payload) == "nord"
    assert parse_theme_bundle({}) is None


def test_split_view_text_caps_huge() -> None:
    assert split_view_text(6_000_000, "abc") == "(huge file - use main pane)"
    assert split_view_text(10, "hello world", cap=5) == "hello"
