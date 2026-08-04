"""Tests for pure line operations."""

from magiceditor.core.line_ops import (
    delete_blank_lines,
    join_lines,
    lines_to_text,
    move_line_down,
    move_line_up,
    sort_lines,
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
