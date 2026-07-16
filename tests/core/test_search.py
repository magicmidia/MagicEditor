"""Search helper tests."""

from __future__ import annotations

from magiceditor.core.search import find_all


def test_find_all_basic() -> None:
    assert find_all(b"ababa", b"aba") == [0]
    assert find_all(b"aaaa", b"aa") == [0, 2]


def test_find_all_empty_needle() -> None:
    assert find_all(b"abc", b"") == []
