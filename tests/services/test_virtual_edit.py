"""Virtual editor edit helpers via Document (no Qt required for replace logic)."""

from __future__ import annotations

from magiceditor.services.document import Document


def test_document_replace_sequence() -> None:
    doc = Document.from_text("foo bar foo")
    # simulate replace_all walking: find 'foo' at 0 and 8
    # delete+insert from end
    doc.delete_bytes(8, 3)
    doc.insert_bytes(8, b"baz")
    doc.delete_bytes(0, 3)
    doc.insert_bytes(0, b"baz")
    assert doc.buffer.get_text() == b"baz bar baz"
    assert doc.line_index().line_count == 1


def test_insert_delete_undo_semantics() -> None:
    doc = Document.from_text("hello")
    doc.insert_bytes(5, b"!")
    assert doc.buffer.get_text() == b"hello!"
    doc.delete_bytes(5, 1)
    assert doc.buffer.get_text() == b"hello"
