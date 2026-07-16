"""Incremental line index updates."""

from __future__ import annotations

from magiceditor.core.line_index import LineIndex
from magiceditor.core.piece_table import PieceTable
from magiceditor.services.document import Document


def test_apply_insert_plain_shifts_starts() -> None:
    idx = LineIndex.from_bytes(b"aaa\nbbb\nccc")
    # insert "XX" at offset 1 (middle of first line)
    idx.apply_insert_plain(1, 2)
    assert idx.line_count == 3
    assert idx.line_start(0) == 0
    assert idx.line_start(1) == 6  # was 4
    assert idx.line_length(0) == 5  # was 3


def test_apply_delete_plain() -> None:
    idx = LineIndex.from_bytes(b"hello\nworld")
    idx.apply_delete_plain(1, 2)  # remove "el"
    assert idx.line_count == 2
    assert idx.line_start(1) == 4  # was 6
    assert idx.line_length(0) == 3


def test_rebuild_suffix_after_newline_insert() -> None:
    table = PieceTable("one\ntwo\nthree")
    idx = LineIndex.from_piece_table(table)
    # insert newline after "one" -> "one\n\ntwo\nthree"
    table.insert(4, b"\n")
    idx.rebuild_suffix(table, 0)
    assert idx.line_count == 4
    assert table.get_text(idx.line_start(1), idx.line_length(1)) == b""
    assert table.get_text(idx.line_start(2), idx.line_length(2)) == b"two"


def test_document_insert_bytes_plain() -> None:
    doc = Document.from_text("hello\nworld")
    idx_before = doc.line_index()
    assert idx_before.line_count == 2
    doc.insert_bytes(5, b"!")  # before \n
    idx = doc.line_index()
    assert idx is idx_before  # same object, mutated
    assert idx.line_count == 2
    assert doc.buffer.get_text() == b"hello!\nworld"
    assert idx.line_start(1) == 7


def test_document_insert_newline_rebuilds() -> None:
    doc = Document.from_text("ab")
    doc.insert_bytes(1, b"\n")
    assert doc.line_index().line_count == 2
    assert doc.line_text(0) == "a"
    assert doc.line_text(1) == "b"


def test_document_delete_newline() -> None:
    doc = Document.from_text("a\nb\nc")
    # delete the first \n
    doc.delete_bytes(1, 1)
    assert doc.buffer.get_text() == b"ab\nc"
    assert doc.line_index().line_count == 2
    assert doc.line_text(0) == "ab"
