"""Unit tests for core.line_filter (P1) — pure, no Qt."""

from __future__ import annotations

import pytest

from magiceditor.core.line_filter import filter_lines, make_matcher
from magiceditor.core.text_match import PatternError


class TestMakeMatcher:
    def test_substring_case_insensitive_default(self) -> None:
        m = make_matcher("error", case_sensitive=False, use_regex=False)
        assert m("an ERROR here")
        assert m("Error")
        assert not m("all good")

    def test_substring_case_sensitive(self) -> None:
        m = make_matcher("Error", case_sensitive=True, use_regex=False)
        assert m("Error")
        assert not m("error")

    def test_substring_is_literal_not_regex(self) -> None:
        m = make_matcher("a.b", case_sensitive=False, use_regex=False)
        assert m("xa.bx")
        assert not m("axb")

    def test_regex(self) -> None:
        m = make_matcher(r"^ERR\d+", case_sensitive=False, use_regex=True)
        assert m("ERR42 boom")
        assert not m("warn ERR")
        assert not m("nope")

    def test_regex_case_sensitive(self) -> None:
        m = make_matcher(r"error", case_sensitive=True, use_regex=True)
        assert m("error")
        assert not m("ERROR")

    def test_invert(self) -> None:
        m = make_matcher("keep", case_sensitive=False, use_regex=False, invert=True)
        assert not m("keep this")
        assert m("drop this")

    def test_invert_regex(self) -> None:
        m = make_matcher(r"^\s*$", case_sensitive=False, use_regex=True, invert=True)
        assert m("content")
        assert not m("   ")

    def test_empty_pattern_raises(self) -> None:
        with pytest.raises(PatternError, match="empty"):
            make_matcher("", case_sensitive=False, use_regex=False)

    def test_invalid_regex_raises_clear_error(self) -> None:
        with pytest.raises(PatternError):
            make_matcher("(unclosed", case_sensitive=False, use_regex=True)

    def test_too_nested_regex_rejected(self) -> None:
        with pytest.raises(PatternError, match="nested"):
            make_matcher("(" * 9, case_sensitive=False, use_regex=True)

    def test_too_long_pattern_rejected(self) -> None:
        with pytest.raises(PatternError, match="longer"):
            make_matcher("x" * 300, case_sensitive=False, use_regex=False)


class TestFilterLines:
    def test_line_numbers_are_1based(self) -> None:
        lines = ["alpha", "beta", "gamma", "beta again"]
        m = make_matcher("beta", case_sensitive=False, use_regex=False)
        assert list(filter_lines(lines, m)) == [(2, "beta"), (4, "beta again")]

    def test_empty_lines(self) -> None:
        lines = ["", "x", ""]
        m = make_matcher("x", case_sensitive=False, use_regex=False)
        assert list(filter_lines(lines, m)) == [(2, "x")]
        # An empty-content matcher via regex still sees empty lines.
        m_empty = make_matcher(r"^$", case_sensitive=False, use_regex=True)
        assert list(filter_lines(lines, m_empty)) == [(1, ""), (3, "")]

    def test_unicode(self) -> None:
        lines = ["olá mundo", "漢字テスト", "sem match", "emoji 🔥"]
        m = make_matcher("漢字", case_sensitive=False, use_regex=False)
        assert list(filter_lines(lines, m)) == [(2, "漢字テスト")]
        m_cf = make_matcher("OLÁ", case_sensitive=False, use_regex=False)
        assert list(filter_lines(lines, m_cf)) == [(1, "olá mundo")]
        m_emoji = make_matcher("🔥", case_sensitive=True, use_regex=False)
        assert list(filter_lines(lines, m_emoji)) == [(4, "emoji 🔥")]

    def test_max_matches_truncates(self) -> None:
        lines = [f"hit {i}" for i in range(10)]
        m = make_matcher("hit", case_sensitive=False, use_regex=False)
        out = list(filter_lines(lines, m, max_matches=3))
        assert out == [(1, "hit 0"), (2, "hit 1"), (3, "hit 2")]

    def test_max_matches_stops_consuming_input(self) -> None:
        consumed = 0

        def gen():
            nonlocal consumed
            for _ in range(100):
                consumed += 1
                yield "hit"

        m = make_matcher("hit", case_sensitive=False, use_regex=False)
        out = list(filter_lines(gen(), m, max_matches=2))
        assert len(out) == 2
        # Generator stops right after the cap — it never drains the source.
        assert consumed == 2

    def test_no_matches(self) -> None:
        m = make_matcher("zzz", case_sensitive=False, use_regex=False)
        assert list(filter_lines(["a", "b"], m)) == []

    def test_invalid_max_matches(self) -> None:
        m = make_matcher("x", case_sensitive=False, use_regex=False)
        with pytest.raises(ValueError, match="max_matches"):
            list(filter_lines(["x"], m, max_matches=0))
