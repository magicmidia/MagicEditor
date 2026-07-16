"""Piece table insert/delete tests."""

from __future__ import annotations

from magiceditor.core.piece_table import PieceTable


def test_insert_middle() -> None:
    table = PieceTable("ace")
    table.insert(1, b"b")
    assert table.get_text() == b"abce"
    table.insert(3, b"d")
    assert table.get_text() == b"abcde"


def test_insert_at_start_and_end() -> None:
    table = PieceTable("mid")
    table.insert(0, b"pre-")
    table.insert(len(table), b"-post")
    assert table.get_text() == b"pre-mid-post"


def test_delete_range() -> None:
    table = PieceTable("abcdef")
    table.delete(2, 2)
    assert table.get_text() == b"abef"
    table.delete(0, 1)
    assert table.get_text() == b"bef"


def test_insert_then_delete_across_pieces() -> None:
    table = PieceTable("hello")
    table.insert(5, b" world")
    table.delete(0, 6)
    assert table.get_text() == b"world"


def test_delete_all() -> None:
    table = PieceTable("x")
    table.delete(0, 1)
    assert len(table) == 0
    assert table.get_text() == b""
