"""Soft-wrap range tests."""

from __future__ import annotations

from magiceditor.core.line_wrap import expand_tabs, wrap_ranges


def _char_width(s: str) -> int:
    return len(s)


def test_no_wrap_short() -> None:
    assert wrap_ranges("hello", 20, _char_width) == [(0, 5)]


def test_wrap_hard() -> None:
    ranges = wrap_ranges("abcdefghij", 4, _char_width)
    assert ranges == [(0, 4), (4, 8), (8, 10)]


def test_wrap_prefers_space() -> None:
    ranges = wrap_ranges("one two three", 8, _char_width)
    # first break after "one " or within limit
    assert ranges[0][0] == 0
    assert ranges[0][1] <= 8
    joined = "".join("one two three"[a:b] for a, b in ranges)
    assert joined == "one two three"


def test_expand_tabs() -> None:
    assert expand_tabs("a\tb") == "a    b"


def test_empty() -> None:
    assert wrap_ranges("", 10, _char_width) == [(0, 0)]
