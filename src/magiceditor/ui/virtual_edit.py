"""Piece-table insert / byte-column mapping for VirtualEditor (J1.1)."""

from __future__ import annotations

from magiceditor.core.text_units import byte_to_column, codec_name, column_to_byte
from magiceditor.ui.virtual_cursors import insert_at_multi_spans

EXPORT_CAP = 2 * 1024 * 1024


def col_to_byte(text: str, col: int, encoding: str) -> int:
    enc = codec_name(encoding)
    return len(text[:col].encode(enc, errors="replace"))


def byte_to_col(text: str, byte_off: int, encoding: str) -> int:
    enc = codec_name(encoding)
    used = 0
    col = 0
    for ch in text:
        b = ch.encode(enc, errors="replace")
        if used + len(b) > byte_off:
            break
        used += len(b)
        col += 1
    return col


def export_text_capped(raw: bytes, total: int, encoding: str, *, limit: int = EXPORT_CAP) -> str:
    enc = codec_name(encoding)
    text = raw.decode(enc, errors="replace")
    if total > limit:
        text += "\n\n… [truncated for export — open smaller range or use external tools]"
    return text


def _line_bytes(editor, line: int) -> bytes:
    idx = editor._doc.line_index()
    start = idx.line_start(line)
    return editor._doc.buffer.get_text(start, idx.line_length(line))


def editor_col_to_byte(editor, line: int, col: int) -> int:
    # Map columns on the raw line. Re-encoding a replace-decoded string turns
    # one bad byte into U+FFFD (3 bytes) and the next delete splits neighbors.
    return column_to_byte(_line_bytes(editor, line), col, editor._doc.encoding)


def editor_byte_to_col(editor, line: int, byte_off: int) -> int:
    return byte_to_column(_line_bytes(editor, line), byte_off, editor._doc.encoding)


def byte_offset_at_cursor(editor) -> int:
    start = editor._doc.line_index().line_start(editor._cursor_line)
    return start + editor_col_to_byte(editor, editor._cursor_line, editor._cursor_col)


def place_cursor_at(editor, byte_off: int) -> None:
    byte_off = max(0, min(len(editor._doc.buffer), byte_off))
    editor._cursor_line = editor._doc.line_index().offset_to_line(byte_off)
    line_start = editor._doc.line_index().line_start(editor._cursor_line)
    editor._cursor_col = editor_byte_to_col(editor, editor._cursor_line, byte_off - line_start)


def emit_edit(editor) -> None:
    editor._modified = True
    editor._update_scrollbars()
    editor.textChanged.emit()
    editor.modificationChanged.emit(True)
    editor.cursorPositionChanged.emit()
    editor.viewport().update()


def insert_at_cursor(editor, text: str) -> None:
    if getattr(editor, "_read_only", False):
        return
    enc = codec_name(editor._doc.encoding)
    data = text.encode(enc, errors="replace")
    if insert_at_multi_spans(editor, text, data):
        return
    off = byte_offset_at_cursor(editor)
    editor._insert_bytes_tracked(off, data)
    editor._clear_selection()
    editor._extra_cursors.clear()
    editor._column_mode = False
    editor._column_anchor = None
    if b"\n" in data or b"\r" in data:
        editor._cursor_line = editor._doc.line_index().offset_to_line(off + len(data))
        line_start = editor._doc.line_index().line_start(editor._cursor_line)
        remain = off + len(data) - line_start
        editor._cursor_col = editor_byte_to_col(editor, editor._cursor_line, remain)
    else:
        editor._cursor_col += len(text)
    emit_edit(editor)


def export_editor_text(editor) -> str:
    limit = EXPORT_CAP
    raw = editor._doc.buffer.get_text(0, min(len(editor._doc.buffer), limit))
    return export_text_capped(raw, len(editor._doc.buffer), editor._doc.encoding, limit=limit)
