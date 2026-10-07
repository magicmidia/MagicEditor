"""Edits beside a rejected byte sequence must not store a new U+FFFD."""

from __future__ import annotations

from magiceditor.core.document_edit import replace_line_range, transform_line_range
from magiceditor.core.line_edit_range import swap_line_with_neighbor
from magiceditor.core.line_ops import join_lines, sort_lines
from magiceditor.core.piece_table import PieceTable
from magiceditor.services.document import Document

_REPL = b"\xef\xbf\xbd"


def _doc(raw: bytes) -> Document:
    return Document(buffer=PieceTable(raw), encoding="utf-8", eol="LF", title="t")


def _raw(doc: Document) -> bytes:
    return doc.buffer.get_text(0, len(doc.buffer))


def test_join_keeps_rejected_bytes() -> None:
    doc = _doc(b"a\xff\nb\n")
    before = _raw(doc).count(_REPL)
    transform_line_range(doc, 0, doc.line_index().line_count, lambda lines: join_lines(lines, " "))
    raw = _raw(doc)
    assert b"\xff" in raw
    assert raw.count(_REPL) == before


def test_sort_and_swap_keep_rejected_bytes() -> None:
    doc = _doc(b"b\na\xff\n")
    transform_line_range(doc, 0, doc.line_index().line_count, sort_lines)
    raw = _raw(doc)
    assert b"\xff" in raw
    assert _REPL not in raw

    swapped = _doc(b"a\xff\nz\n")
    swap_line_with_neighbor(swapped, 0, up=False)
    raw = _raw(swapped)
    assert raw.startswith(b"z\n")
    assert b"\xff" in raw
    assert _REPL not in raw


def test_neighbor_insert_delete_split_and_replace_keep_rejected_bytes() -> None:
    doc = _doc(b"a\xffb")
    doc.insert_bytes(0, b"Z")
    assert _raw(doc) == b"Za\xffb"
    doc.delete_bytes(0, 1)
    assert _raw(doc) == b"a\xffb"
    doc.insert_bytes(1, b"\n")
    assert _raw(doc) == b"a\n\xffb"
    assert _REPL not in _raw(doc)

    other = _doc(b"a\xff\nkeep\n")
    replace_line_range(other, 1, 2, ["KEEP"])
    raw = _raw(other)
    assert b"\xff" in raw
    assert b"KEEP" in raw
    assert _REPL not in raw
