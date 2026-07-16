"""Piece table unit tests."""

from __future__ import annotations

from magiceditor.core.piece_table import PieceTable


def test_empty_table_has_zero_length() -> None:
    assert len(PieceTable()) == 0


def test_original_text_roundtrip() -> None:
    table = PieceTable("hello")
    assert len(table) == 5
    assert table.get_text() == b"hello"


def test_get_text_slice() -> None:
    table = PieceTable("abcdef")
    assert table.get_text(1, 3) == b"bcd"
