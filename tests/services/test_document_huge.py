"""Huge-file open policy."""

from __future__ import annotations

from pathlib import Path

from magiceditor.services.document_io import UI_VIRTUAL_THRESHOLD_BYTES, open_document


def test_virtual_threshold_document(tmp_path: Path) -> None:
    # Just above UI virtual threshold but well below mmap threshold
    size = UI_VIRTUAL_THRESHOLD_BYTES + 1024
    path = tmp_path / "big.txt"
    path.write_bytes(b"x" * size + b"\nline2\n")
    doc = open_document(path)
    assert doc.huge_mode is True
    assert doc.line_index().line_count >= 2
    # first line content is all x's
    assert doc.line_text(0).startswith("x")
    doc.close()


def test_small_document_not_huge(tmp_path: Path) -> None:
    path = tmp_path / "small.txt"
    path.write_text("hello\nworld\n", encoding="utf-8")
    doc = open_document(path)
    assert doc.huge_mode is False
    assert "hello" in doc.text()
