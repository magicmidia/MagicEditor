"""Tests for core.text_stats — streaming text statistics."""

from __future__ import annotations

from magiceditor.core.text_stats import TextStats, compute_stats, stats_for_text


def test_simple_text():
    stats = stats_for_text("hello world")
    assert stats == TextStats(
        chars=11,
        chars_no_spaces=10,
        words=2,
        lines=1,
        non_empty_lines=1,
    )


def test_empty_text():
    assert stats_for_text("") == TextStats()
    assert compute_stats([]) == TextStats()
    assert compute_stats(["", ""]) == TextStats()


def test_crlf_counts_as_single_line_break():
    stats = stats_for_text("a\r\nb\r\n")
    assert stats.chars == 6
    assert stats.lines == 2
    assert stats.non_empty_lines == 2
    assert stats.words == 2


def test_crlf_split_between_chunks():
    stats = compute_stats(["a\r", "\nb"])
    assert stats.chars == 4
    assert stats.lines == 2
    assert stats.non_empty_lines == 2
    assert stats.words == 2


def test_lf_only_lines():
    stats = stats_for_text("one\ntwo\nthree")
    assert stats.lines == 3
    assert stats.non_empty_lines == 3
    assert stats.words == 3


def test_word_split_between_chunks():
    stats = compute_stats(["hel", "lo wor", "ld"])
    assert stats.words == 2
    assert stats.chars == 11
    assert stats.chars_no_spaces == 10


def test_word_split_with_space_at_chunk_boundary():
    stats = compute_stats(["foo ", " bar"])
    assert stats.words == 2
    stats2 = compute_stats(["foo", " ", "bar"])
    assert stats2.words == 2


def test_unicode_text():
    stats = stats_for_text("café ação")
    assert stats.chars == 9
    assert stats.chars_no_spaces == 8
    assert stats.words == 2
    assert stats.lines == 1


def test_final_line_without_newline_counts():
    stats = stats_for_text("a\nb")
    assert stats.lines == 2
    assert stats.non_empty_lines == 2


def test_trailing_newline_does_not_add_line():
    stats = stats_for_text("a\n")
    assert stats.lines == 1
    assert stats.non_empty_lines == 1


def test_whitespace_only_line_not_non_empty():
    stats = stats_for_text("a\n  \nb")
    assert stats.lines == 3
    assert stats.non_empty_lines == 2


def test_tabs_and_multiple_spaces():
    stats = stats_for_text("foo\t  bar   ")
    assert stats.words == 2
    assert stats.chars_no_spaces == 6


def test_many_chunks_same_as_single():
    text = "um dois três\nquatro\r\ncinco\n\nseis"
    single = stats_for_text(text)
    chunked = compute_stats(list(text))  # one char per chunk
    assert chunked == single
    assert single.lines == 5
    assert single.non_empty_lines == 4
    assert single.words == 6
