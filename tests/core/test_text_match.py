"""Pattern compile / match helpers."""

from __future__ import annotations

import pytest

from magiceditor.core.text_match import (
    PatternError,
    compile_pattern,
    expand_replacement,
    find_all_matches,
    find_first,
    find_last_before,
)


def test_literal_escape() -> None:
    pat = compile_pattern(r"a+b", use_regex=False)
    assert pat.search("xa+by")
    assert not pat.search("xaaby")


def test_regex() -> None:
    pat = compile_pattern(r"\d+", use_regex=True)
    m = find_first("ab12cd", pat)
    assert m is not None
    assert m.group() == "12"


def test_case_insensitive() -> None:
    pat = compile_pattern("Hello", case_sensitive=False, use_regex=False)
    assert find_first("say hello", pat) is not None


def test_bad_regex() -> None:
    with pytest.raises(PatternError):
        compile_pattern("(", use_regex=True)


def test_find_last_before() -> None:
    pat = compile_pattern("a", use_regex=False)
    m = find_last_before("a x a y", pat, before=4)
    assert m is not None
    assert m.start() == 0
    m2 = find_last_before("a x a y", pat, before=5)
    assert m2 is not None
    assert m2.start() == 4


def test_expand_replacement() -> None:
    pat = compile_pattern(r"(\w+)=(\w+)", use_regex=True)
    m = pat.search("foo=bar")
    assert m is not None
    assert expand_replacement(m, r"\2:\1") == "bar:foo"


def test_find_all() -> None:
    pat = compile_pattern(r"\d+", use_regex=True)
    assert [m.group() for m in find_all_matches("a1b22c", pat)] == ["1", "22"]
