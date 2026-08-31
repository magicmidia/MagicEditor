"""Open/save documents with size-aware loading policy."""

from __future__ import annotations

from pathlib import Path

from magiceditor.core.document import Document
from magiceditor.core.encoding import decode_bytes, encode_text, normalize_newlines
from magiceditor.core.line_index import LineIndex
from magiceditor.core.mmap_source import MmapSource, should_use_mmap
from magiceditor.core.piece_table import PieceTable
from magiceditor.core.syntax_limits import HUGE_UI_BYTES, PROBE_BYTES, syntax_enabled_for_size
from magiceditor.services.atomic_io import write_bytes_atomic, write_chunks_atomic

# Soft UI threshold: above this size use VirtualEditor (no full QTextDocument).
UI_VIRTUAL_THRESHOLD_BYTES = HUGE_UI_BYTES


def open_document(path: Path | str) -> Document:
    """Open a file into a Document.

    * ``size > 5MB`` → memory-map (no full RAM copy of the file).
    * ``size > 5MB`` → huge_mode (viewport UI).
    * smaller files → full decode into the piece table (still VirtualEditor).
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
            syntax_enabled=syntax_enabled_for_size(size),
            _mmap=src,
            _line_index=index,
        )

    raw = path.read_bytes()
    probe = decode_bytes(raw[:PROBE_BYTES] if len(raw) > PROBE_BYTES else raw)
    huge = size > UI_VIRTUAL_THRESHOLD_BYTES
    syntax_on = syntax_enabled_for_size(size)
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
            syntax_enabled=syntax_on,
            _line_index=index,
        )

    # Probe is encoding/EOL only (K9). Keep the full raw in the piece table.
    return Document(
        buffer=PieceTable(raw),
        path=path,
        encoding=probe.encoding,
        eol=probe.eol,
        title=title,
        huge_mode=False,
        syntax_enabled=syntax_on,
    )


def save_document(document: Document, path: Path | str | None = None) -> Document:
    """Write document bytes to disk. Updates path/title when saving as."""
    target = Path(path) if path is not None else document.path
    if target is None:
        raise ValueError("No path for save")

    if document.huge_mode:
        chunks = document.buffer.iter_chunks()
        if document.encoding == "utf-8-sig":
            first = True

            def _bom_chunks():
                nonlocal first
                for chunk in chunks:
                    if first:
                        first = False
                        if not chunk.startswith(b"\xef\xbb\xbf"):
                            yield b"\xef\xbb\xbf" + chunk
                            continue
                    yield chunk

            write_chunks_atomic(target, _bom_chunks())
        else:
            write_chunks_atomic(target, chunks)
    else:
        # Re-encode from text so Format → Encoding is honored on save.
        text = document.text()
        data = encode_text(text, document.encoding)
        if document.eol in {"LF", "CRLF", "CR"}:
            data = normalize_newlines(data, document.eol)
        write_bytes_atomic(target, data)
    document.path = target
    document.title = target.name
    document.modified = False
    return document
