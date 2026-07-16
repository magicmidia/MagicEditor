"""Line index tests."""

from __future__ import annotations

from magiceditor.core.line_index import LineIndex
from magiceditor.core.piece_table import PieceTable


def test_single_line() -> None:
    idx = LineIndex.from_bytes(b"hello")
    assert idx.line_count == 1
    assert idx.line_start(0) == 0
    assert idx.line_length(0) == 5


def test_multiple_lines_lf() -> None:
    idx = LineIndex.from_bytes(b"a\nb\nc")
    assert idx.line_count == 3
    assert idx.line_start(1) == 2
    assert idx.offset_to_line(2) == 1
    assert idx.offset_to_line(4) == 2


def test_crlf() -> None:
    idx = LineIndex.from_bytes(b"a\r\nb\r\n")
    assert idx.line_count == 3
    assert idx.line_start(1) == 3
    assert idx.line_length(0) == 1


def test_from_piece_table() -> None:
    table = PieceTable("one\ntwo\nthree")
    idx = LineIndex.from_piece_table(table)
    assert idx.line_count == 3
    assert table.get_text(idx.line_start(1), idx.line_length(1)) == b"two"
