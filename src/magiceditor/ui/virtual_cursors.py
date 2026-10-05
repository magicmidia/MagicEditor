"""Column / multi-cursor span helpers (no Qt)."""

from __future__ import annotations

from magiceditor.core.multi_cursor import restore_carets_after_multi_insert
from magiceditor.core.text_units import grapheme_end, grapheme_start

Span = tuple[int, int, int]


def column_rect(
    *,
    column_mode: bool,
    has_selection: bool,
    sel: tuple[int, int, int, int] | None,
) -> tuple[int, int, int, int] | None:
    """Return (start_line, end_line, col0, col1) or None."""
    if not column_mode or not has_selection or sel is None:
        return None
    s_line, s_col, e_line, e_col = sel
    c0, c1 = min(s_col, e_col), max(s_col, e_col)
    return s_line, e_line, c0, c1


def multi_edit_spans(
    *,
    column_mode: bool,
    has_selection: bool,
    sel: tuple[int, int, int, int] | None,
    extra_cursors: list[Span],
    cursor_line: int,
    cursor_col: int,
) -> list[Span]:
    """Spans (line, start_col, end_col) bottom-to-top for multi edits."""
    col = column_rect(column_mode=column_mode, has_selection=has_selection, sel=sel)
    if col is not None:
        s_line, e_line, c0, c1 = col
        spans = [(ln, c0, c1) for ln in range(s_line, e_line + 1)]
        spans.sort(key=lambda t: (t[0], t[1]), reverse=True)
        return spans
    if extra_cursors:
        spans: list[Span] = []
        if has_selection and sel is not None:
            s_line, s_col, e_line, e_col = sel
            if s_line == e_line:
                spans.append((s_line, s_col, e_col))
            else:
                return []
        else:
            spans.append((cursor_line, cursor_col, cursor_col))
        spans.extend(extra_cursors)
        seen: set[Span] = set()
        uniq: list[Span] = []
        for sp in spans:
            if sp not in seen:
                seen.add(sp)
                uniq.append(sp)
        uniq.sort(key=lambda t: (t[0], t[1]), reverse=True)
        return uniq
    return []


def editor_selection(editor) -> tuple[int, int, int, int] | None:
    if not editor.has_selection():
        return None
    return editor._normalized_selection()


def editor_column_rect(editor) -> tuple[int, int, int, int] | None:
    return column_rect(
        column_mode=editor._column_mode,
        has_selection=editor.has_selection(),
        sel=editor_selection(editor),
    )


def editor_multi_spans(editor) -> list[Span]:
    return multi_edit_spans(
        column_mode=editor._column_mode,
        has_selection=editor.has_selection(),
        sel=editor_selection(editor),
        extra_cursors=list(editor._extra_cursors),
        cursor_line=editor._cursor_line,
        cursor_col=editor._cursor_col,
    )


def insert_at_multi_spans(editor, text: str, data: bytes) -> bool:
    """Insert ``text`` at every multi/column span. False if not a multi edit."""
    spans = editor_multi_spans(editor)
    if not spans or b"\n" in data or b"\r" in data:
        return False
    was_column = editor._column_mode
    post_carets: list[tuple[int, int]] = []
    for line, c0, c1 in spans:
        line_text = editor._doc.line_text(line)
        if c0 > len(line_text):
            pad = c0 - len(line_text)
            pad_off = editor._doc.line_index().line_start(line) + editor._col_to_byte(
                line, len(line_text)
            )
            editor._insert_bytes_tracked(pad_off, b" " * pad)
            line_text = editor._doc.line_text(line)
        a = min(c0, len(line_text))
        b = min(max(c1, c0), len(editor._doc.line_text(line)))
        start = editor._doc.line_index().line_start(line) + editor._col_to_byte(line, a)
        if b > a:
            end = editor._doc.line_index().line_start(line) + editor._col_to_byte(line, b)
            editor._delete_bytes_tracked(start, end - start)
        editor._insert_bytes_tracked(start, data)
        post_carets.append((line, a + len(text)))
    primary, extras = restore_carets_after_multi_insert(post_carets)
    editor._cursor_line, editor._cursor_col = primary
    editor._extra_cursors = list(extras)
    editor._clear_selection()
    if was_column and len(post_carets) > 1:
        sorted_carets = sorted(post_carets, key=lambda t: (t[0], t[1]))
        editor._column_mode = True
        editor._column_anchor = sorted_carets[0]
        editor._anchor_line = sorted_carets[0][0]
        editor._anchor_col = sorted_carets[0][1]
    else:
        editor._column_mode = False
        editor._column_anchor = None
    editor._emit_edit()
    return True


def backspace(editor) -> None:
    if editor.has_selection() or editor._extra_cursors or editor_column_rect(editor):
        spans = editor_multi_spans(editor)
        if spans and all(c0 == c1 for _, c0, c1 in spans):
            rebuilt: list[tuple[int, int, int]] = []
            for line, c0, _c1 in spans:
                if c0 <= 0:
                    rebuilt.append((line, 0, 0))
                    continue
                text = editor._doc.line_text(line)
                clamped = min(c0, len(text))
                cut = grapheme_start(text, clamped)
                start = editor._doc.line_index().line_start(line) + editor._col_to_byte(line, cut)
                end = editor._doc.line_index().line_start(line) + editor._col_to_byte(line, clamped)
                if end > start:
                    editor._delete_bytes_tracked(start, end - start)
                rebuilt.append((line, cut, cut))
            rebuilt.sort(key=lambda t: (t[0], t[1]))
            if rebuilt:
                editor._cursor_line, editor._cursor_col, _ = rebuilt[-1]
                editor._extra_cursors = [(ln, c, c) for ln, c, _ in rebuilt[:-1]]
            editor._clear_selection()
            editor._emit_edit()
            return
        editor._delete_selection()
        return
    off = editor._byte_offset_at_cursor()
    if off <= 0:
        return
    idx = editor._doc.line_index()
    line = editor._cursor_line
    col = editor._cursor_col
    if col > 0:
        # Erase the whole grapheme left of the caret, measured on raw bytes
        # so a broken UTF-8 byte is removed once and not rewritten as U+FFFD.
        text = editor._doc.line_text(line)
        col = min(col, len(text))
        cut = grapheme_start(text, col)
        start = idx.line_start(line) + editor._col_to_byte(line, cut)
        off = idx.line_start(line) + editor._col_to_byte(line, col)
    else:
        # Caret at column 0: join with the previous line by removing the
        # entire line terminator ("\n", "\r\n", or UTF-16 units).
        prev = line - 1
        start = idx.line_start(prev) + idx.line_length(prev)
    if off > start:
        editor._delete_bytes_tracked(start, off - start)
    editor._place_cursor_at(start)
    editor._clear_selection()
    editor._emit_edit()


def delete_forward(editor) -> None:
    if editor.has_selection() or editor._extra_cursors or editor_column_rect(editor):
        spans = editor_multi_spans(editor)
        if spans and all(c0 == c1 for _, c0, c1 in spans):
            for line, c0, _c1 in spans:
                text = editor._doc.line_text(line)
                if c0 >= len(text):
                    continue
                end_col = grapheme_end(text, c0)
                start = editor._doc.line_index().line_start(line) + editor._col_to_byte(line, c0)
                end = editor._doc.line_index().line_start(line) + editor._col_to_byte(line, end_col)
                if end > start:
                    editor._delete_bytes_tracked(start, end - start)
            editor._clear_selection()
            editor._emit_edit()
            return
        editor._delete_selection()
        return
    off = editor._byte_offset_at_cursor()
    if off >= len(editor._doc.buffer):
        return
    idx = editor._doc.line_index()
    line = editor._cursor_line
    col = editor._cursor_col
    text = editor._doc.line_text(line)
    line_start = idx.line_start(line)
    if col < len(text):
        # Erase the whole grapheme under the caret (multibyte-safe).
        end_col = grapheme_end(text, col)
        start = line_start + editor._col_to_byte(line, col)
        end = line_start + editor._col_to_byte(line, end_col)
    else:
        # Caret at EOL: remove the entire line terminator, joining lines.
        start = line_start + idx.line_length(line)
        end = idx.line_start(line + 1) if line + 1 < editor._line_count() else start
    if end > start:
        editor._delete_bytes_tracked(start, end - start)
    editor._clear_selection()
    editor._emit_edit()


def duplicate_current_line(editor) -> None:
    text = editor._doc.line_text(editor._cursor_line)
    enc = editor._doc.encoding if editor._doc.encoding != "utf-8-sig" else "utf-8"
    line = editor._cursor_line
    total = editor._line_count()
    if line < total - 1:
        off = editor._doc.line_index().line_start(line + 1)
        data = (text + "\n").encode(enc, errors="replace")
    else:
        off = len(editor._doc.buffer)
        data = ("\n" + text).encode(enc, errors="replace")
    editor._insert_bytes_tracked(off, data)
    editor._clear_selection()
    editor._emit_edit()
