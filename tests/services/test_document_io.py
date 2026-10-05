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


def test_open_midsize_file_keeps_full_buffer(tmp_path: Path) -> None:
    """K9: probe is encoding-only; 64KB < size ≤ 5MB must keep every byte."""
    path = tmp_path / "mid.txt"
    tail = "LAST-LINE-MARKER\n"
    body = ("HEAD\n" + ("x" * (80 * 1024)) + "\n" + tail).encode("utf-8")
    path.write_bytes(body)
    size = path.stat().st_size
    assert 64 * 1024 < size <= 5 * 1024 * 1024
    doc = open_document(path)
    assert len(doc.buffer) == size
    raw = doc.buffer.get_text(0, len(doc.buffer))
    assert raw == body
    assert b"LAST-LINE-MARKER" in raw
    assert raw.endswith(b"LAST-LINE-MARKER\n")


def test_huge_save_writes_chunks(tmp_path: Path) -> None:
    path = tmp_path / "huge.txt"
    doc = Document.from_text("chunk-save\n")
    doc.huge_mode = True
    save_document(doc, path)
    assert b"chunk-save" in path.read_bytes()


def test_mmap_save_in_place(tmp_path: Path) -> None:
    """Ensure saving a modified mmapped file (>5MB) replaces in place without lock errors."""
    path = tmp_path / "big_mmap.txt"
    line = b"Line 0123456789\n"
    count = (6 * 1024 * 1024) // len(line)
    path.write_bytes(line * count)

    doc = open_document(path)
    try:
        assert doc.huge_mode is True
        assert doc._mmap is not None
        doc.insert_bytes(0, b"HEADER_PREFIX\n")
        save_document(doc)
        assert doc.modified is False
        assert doc.line_text(0) == "HEADER_PREFIX"
    finally:
        doc.close()
