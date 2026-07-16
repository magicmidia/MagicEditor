"""Open/save documents with size-aware loading policy."""

from __future__ import annotations

from pathlib import Path

from magiceditor.core.encoding import decode_bytes
from magiceditor.core.mmap_source import MmapSource, should_use_mmap
from magiceditor.core.piece_table import PieceTable
from magiceditor.services.document import Document

# Soft cap for decoding entire huge files into a str for the QPlainTextEdit MVP path.
# Above mmap threshold we still open via mmap but materialize only if needed.
_MAX_EDITABLE_DECODE = 50 * 1024 * 1024


def open_document(path: Path | str) -> Document:
    """Open a file into a Document.

    Files above the mmap threshold are memory-mapped for the initial read.
    The MVP still builds a piece table from the full byte content so editing
    works; a future milestone will stream viewport slices without full decode.
    """
    path = Path(path)
    size = path.stat().st_size

    if should_use_mmap(path, size):
        with MmapSource(path) as src:
            raw = src.read_all()
    else:
        raw = path.read_bytes()

    if size > _MAX_EDITABLE_DECODE:
        # Keep bytes in piece table; decode lazily for small slices later.
        # For UI MVP, decode with replace so the editor can still show something.
        probe = decode_bytes(raw)
        doc = Document(
            buffer=PieceTable(raw),
            path=path,
            encoding=probe.encoding,
            eol=probe.eol,
            title=path.name,
        )
        return doc

    probe = decode_bytes(raw)
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

    text = document.text()
    enc = document.encoding
    if enc == "utf-8-sig":
        data = text.encode("utf-8-sig")
    else:
        data = text.encode(enc, errors="replace")

    # Normalize EOL on save for non-mixed documents
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
