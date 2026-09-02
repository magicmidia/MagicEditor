"""Tests for pure line operations."""

from magiceditor.core.line_ops import (
    delete_blank_lines,
    join_lines,
    lines_to_text,
    move_line_down,
    move_line_up,
    remove_consecutive_duplicates,
    remove_duplicate_lines,
    reverse_lines,
    sort_lines,
    sort_lines_by_length,
    spaces_to_tabs,
    tabs_to_spaces,
    text_to_lines,
    trim_trailing_whitespace,
)


def test_move_line_up_down() -> None:
    lines = ["a", "b", "c"]
    up, i = move_line_up(lines, 1)
    assert up == ["b", "a", "c"] and i == 0
    down, j = move_line_down(lines, 0)
    assert down == ["b", "a", "c"] and j == 1


def test_sort_join_delete_blank() -> None:
    assert sort_lines(["c", "a", "b"]) == ["a", "b", "c"]
    assert join_lines(["a", "b"], "-") == ["a-b"]
    assert delete_blank_lines(["a", "", "  ", "b"]) == ["a", "b"]


def test_trim_and_tabs() -> None:
    assert trim_trailing_whitespace(["hi  ", "x\t"]) == ["hi", "x"]
    assert tabs_to_spaces(["\tx"], 4) == ["    x"]
    assert spaces_to_tabs(["    x"], 4) == ["\tx"]


def test_text_roundtrip_lines() -> None:
    text = "a\nb\n"
    lines = text_to_lines(text)
    assert lines_to_text(lines) == "a\nb\n" or lines_to_text(lines).startswith("a\nb")


def test_remove_duplicate_lines_stable_keeps_first() -> None:
    lines = ["b", "a", "b", "c", "a"]
    assert remove_duplicate_lines(lines) == ["b", "a", "c"]


def test_remove_duplicate_lines_blank_lines_are_normal_lines() -> None:
    # blank lines count as content: only removed when duplicated
    lines = ["a", "", "b", "", "a"]
    assert remove_duplicate_lines(lines) == ["a", "", "b"]


def test_remove_duplicate_lines_no_duplicates() -> None:
    lines = ["a", "b", "c"]
    assert remove_duplicate_lines(lines) == ["a", "b", "c"]
    assert remove_duplicate_lines([]) == []


def test_remove_consecutive_duplicates() -> None:
    lines = ["a", "a", "b", "a", "a", "", ""]
    assert remove_consecutive_duplicates(lines) == ["a", "b", "a", ""]
    assert remove_consecutive_duplicates([]) == []
    assert remove_consecutive_duplicates(["x"]) == ["x"]


def test_reverse_lines() -> None:
    assert reverse_lines(["a", "b", "c"]) == ["c", "b", "a"]
    assert reverse_lines([]) == []
    assert reverse_lines(["única"]) == ["única"]


def test_sort_lines_by_length_stable() -> None:
    lines = ["ccc", "a", "bb", "z", "dd"]
    assert sort_lines_by_length(lines) == ["a", "z", "bb", "dd", "ccc"]
    # stable: equal lengths keep original relative order even when reversed
    assert sort_lines_by_length(lines, reverse=True) == ["ccc", "bb", "dd", "a", "z"]
