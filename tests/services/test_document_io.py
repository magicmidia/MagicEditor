"""Document open/save tests."""

from __future__ import annotations

from pathlib import Path

from magiceditor.services.document import Document
from magiceditor.services.document_io import open_document, save_document


def test_open_and_save_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "sample.txt"
    path.write_text("hello\nworld\n", encoding="utf-8")
    doc = open_document(path)
    assert "hello" in doc.text()
    assert doc.eol in {"LF", "CRLF", "MIXED", "NONE"}

    doc.buffer.insert(len(doc.buffer), b"!")
    doc.mark_modified()
    out = tmp_path / "out.txt"
    save_document(doc, out)
    saved = out.read_text(encoding="utf-8-sig")
    assert saved.lstrip("\ufeff").startswith("hello")


def test_blank_document() -> None:
    doc = Document.blank()
    assert doc.path is None
    assert len(doc.buffer) == 0
