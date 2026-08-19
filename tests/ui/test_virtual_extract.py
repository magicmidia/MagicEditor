"""Drive J1.1 extracted units without mocking them (no display)."""

from __future__ import annotations

from magiceditor.core.text_match import compile_pattern
from magiceditor.ui.virtual_clipboard import normalized_selection
from magiceditor.ui.virtual_cursors import column_rect, multi_edit_spans
from magiceditor.ui.virtual_edit import byte_to_col, col_to_byte, export_text_capped
from magiceditor.ui.virtual_find import (
    FindHit,
    collect_replace_jobs,
    count_matches_in_lines,
    find_next_in_lines,
)
from magiceditor.ui.virtual_keys import indent_insert_text, newline_payload
from magiceditor.ui.virtual_undo import UndoHistory, apply_redo_op, apply_undo_op


def test_col_to_byte_and_back_handles_utf8() -> None:
    text = "ação"
    off = col_to_byte(text, 2, "utf-8")
    assert off == len("aç".encode())
    assert byte_to_col(text, off, "utf-8") == 2
    assert col_to_byte("ab", 2, "utf-8-sig") == 2


def test_export_text_capped_marks_truncation() -> None:
    raw = b"hello"
    out = export_text_capped(raw, total=3_000_000, encoding="utf-8", limit=4)
    assert out.startswith("hell")
    assert "truncated" in out


def test_normalized_selection_orders_anchor() -> None:
    assert normalized_selection(2, 5, 0, 1) == (0, 1, 2, 5)
    assert normalized_selection(0, 1, 2, 5) == (0, 1, 2, 5)


def test_newline_payload_python_block() -> None:
    assert newline_payload("def foo():", 10, "python", spaces=True, width=4) == "\n    "
    assert newline_payload("    if x:", 9, "python", spaces=True, width=4) == "\n        "
    assert newline_payload("    x = 1", 9, "python", spaces=True, width=4) == "\n    "


def test_newline_payload_at_column_zero_ignores_rest_of_line() -> None:
    """Enter at col 0 must not treat the remainder as a block opener."""
    assert newline_payload("def foo():", 0, "python", spaces=True, width=4) == "\n"
    assert newline_payload("    if x:", 0, "python", spaces=True, width=4) == "\n"


def test_indent_insert_text_spaces_and_tab() -> None:
    assert indent_insert_text(spaces=True, width=4) == "    "
    assert indent_insert_text(spaces=False, width=4) == "\t"


def test_find_next_in_lines_wraps_and_skips_current() -> None:
    lines = ["abc def", "xyz abc"]

    def line_text(i: int) -> str:
        return lines[i]

    pat = compile_pattern("abc")
    hit = find_next_in_lines(
        line_text,
        2,
        pat,
        start_line=0,
        start_col=0,
        last_match_start=0,
        last_match_end=3,
    )
    assert hit == FindHit(1, 4, 7)


def test_count_matches_in_lines_does_not_join_buffer() -> None:
    lines = ["aa x aa", "zz", "aa"]
    seen: list[int] = []

    def line_text(i: int) -> str:
        seen.append(i)
        return lines[i]

    pat = compile_pattern("aa")
    assert count_matches_in_lines(line_text, 3, pat) == 3
    assert seen == [0, 1, 2]


def test_collect_replace_jobs_reverse_order() -> None:
    lines = ["aa x aa", "aa"]

    def line_text(i: int) -> str:
        return lines[i]

    pat = compile_pattern("aa")
    jobs = collect_replace_jobs(line_text, 2, pat, "b")
    assert jobs == [(1, 0, 2, "b"), (0, 5, 7, "b"), (0, 0, 2, "b")]


def test_undo_history_insert_delete_roundtrip() -> None:
    buf = bytearray(b"hi")
    hist = UndoHistory()

    def insert(offset: int, data: bytes) -> None:
        buf[offset:offset] = data

    def delete(offset: int, length: int) -> None:
        del buf[offset : offset + length]

    insert(2, b"!")
    hist.record_insert(2, b"!")
    assert bytes(buf) == b"hi!"

    op = hist.pop_undo()
    assert op is not None
    apply_undo_op(op, insert_bytes=insert, delete_bytes=delete)
    hist.remember_undone(op)
    assert bytes(buf) == b"hi"

    op = hist.pop_redo()
    assert op is not None
    apply_redo_op(op, insert_bytes=insert, delete_bytes=delete)
    assert bytes(buf) == b"hi!"


def test_multi_edit_spans_column_and_extras() -> None:
    col = column_rect(
        column_mode=True,
        has_selection=True,
        sel=(1, 2, 3, 5),
    )
    assert col == (1, 3, 2, 5)
    spans = multi_edit_spans(
        column_mode=True,
        has_selection=True,
        sel=(1, 2, 3, 5),
        extra_cursors=[],
        cursor_line=3,
        cursor_col=5,
    )
    assert spans == [(3, 2, 5), (2, 2, 5), (1, 2, 5)]

    extras = multi_edit_spans(
        column_mode=False,
        has_selection=False,
        sel=None,
        extra_cursors=[(0, 1, 1), (2, 0, 2)],
        cursor_line=4,
        cursor_col=0,
    )
    assert extras[0][0] >= extras[-1][0]
    assert (4, 0, 0) in extras
    assert (2, 0, 2) in extras
