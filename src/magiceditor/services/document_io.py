"""Open/save documents with size-aware loading policy."""

from __future__ import annotations

from pathlib import Path

from magiceditor.core.encoding import decode_bytes
from magiceditor.core.line_index import LineIndex
from magiceditor.core.mmap_source import MmapSource, should_use_mmap
from magiceditor.core.piece_table import PieceTable
from magiceditor.services.document import Document

# Soft UI threshold: above this size use VirtualEditor (no full QTextDocument).
UI_VIRTUAL_THRESHOLD_BYTES = 5 * 1024 * 1024


def open_document(path: Path | str) -> Document:
    """Open a file into a Document.

    * ``size > 50MB`` → memory-map (no full RAM copy of the file).
    * ``size > 5MB`` → huge_mode (viewport UI).
    * smaller files → full decode into piece table for the classic editor.
    """
    path = Path(path)
    size = path.stat().st_size
    title = path.name

    if should_use_mmap(path, size):
        src = MmapSource(path)
        view = src.as_memoryview()
        sample_n = min(len(view), 64 * 1024)
        sample = bytes(view[:sample_n]) if sample_n else b""
        probe = decode_bytes(sample if sample else b"\n")
        table = PieceTable(view)
        index = LineIndex.from_buffer(view)
        return Document(
            buffer=table,
            path=path,
            encoding=probe.encoding,
            eol=probe.eol,
            title=title,
            huge_mode=True,
            _mmap=src,
            _line_index=index,
        )

    raw = path.read_bytes()
    probe = decode_bytes(raw)
    huge = size > UI_VIRTUAL_THRESHOLD_BYTES
    if huge:
        table = PieceTable(raw)
        index = LineIndex.from_bytes(raw)
        return Document(
            buffer=table,
            path=path,
            encoding=probe.encoding,
            eol=probe.eol,
            title=title,
            huge_mode=True,
            _line_index=index,
        )

    return Document.from_text(
        probe.text,
        path=path,
        encoding=probe.encoding,
        eol=probe.eol,
    )


def save_document(document: Document, path: Path | str | None = None) -> Document:
    """Write document bytes to disk. Updates path/title when saving as."""
    target = Path(path) if path is not None else document.path
    if target is None:
        raise ValueError("No path for save")

    # Prefer raw buffer bytes (works for huge_mode without re-encoding surprises).
    data = document.buffer.get_text()
    if document.encoding == "utf-8-sig" and not data.startswith(b"\xef\xbb\xbf"):
        data = b"\xef\xbb\xbf" + data

    # Normalize EOL for non-mixed documents when not huge (cheap on small files).
    if not document.huge_mode:
        if document.eol == "CRLF":
            data = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        elif document.eol == "LF":
            data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        elif document.eol == "CR":
            data = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r")

    target.write_bytes(data)
    document.path = target
    document.title = target.name
    document.modified = False
    return document
