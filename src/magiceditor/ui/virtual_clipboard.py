"""Selection + clipboard for VirtualEditor (J1.1)."""

from __future__ import annotations

from PyQt6.QtGui import QGuiApplication

MAX_CLIPBOARD = 8 * 1024 * 1024


def normalized_selection(
    anchor_line: int, anchor_col: int, cursor_line: int, cursor_col: int
) -> tuple[int, int, int, int]:
    a = (anchor_line, anchor_col)
    b = (cursor_line, cursor_col)
    if a <= b:
        return a[0], a[1], b[0], b[1]
    return b[0], b[1], a[0], a[1]


def has_selection(editor) -> bool:
    return editor._anchor_line is not None and (
        editor._anchor_line != editor._cursor_line or editor._anchor_col != editor._cursor_col
    )


def clear_selection(editor) -> None:
    editor._anchor_line = None
    editor._anchor_col = 0


def editor_normalized_selection(editor) -> tuple[int, int, int, int]:
    assert editor._anchor_line is not None
    return normalized_selection(
        editor._anchor_line, editor._anchor_col, editor._cursor_line, editor._cursor_col
    )


def selection_cols_on_line(editor, line: int) -> tuple[int, int] | None:
    if not has_selection(editor):
        for el, esc, eec in editor._extra_cursors:
            if el == line and eec > esc:
                return esc, eec
        return None
    col = editor._column_rect()
    if col is not None:
        s_line, e_line, c0, c1 = col
        if line < s_line or line > e_line:
            return None
        text = editor._doc.line_text(line)
        a = min(c0, len(text))
        b = min(c1, len(text))
        if a >= b:
            return None
        return a, b
    s_line, s_col, e_line, e_col = editor_normalized_selection(editor)
    if line < s_line or line > e_line:
        return None
    a = s_col if line == s_line else 0
    b = e_col if line == e_line else len(editor._doc.line_text(line))
    if a >= b:
        return None
    return a, b


def selected_text(editor) -> str:
    if not has_selection(editor):
        return ""
    s_line, s_col, e_line, e_col = editor_normalized_selection(editor)
    if s_line == e_line:
        return editor._doc.line_text(s_line)[s_col:e_col]
    parts: list[str] = [editor._doc.line_text(s_line)[s_col:]]
    max_lines = 50_000
    for ln in range(s_line + 1, min(e_line, s_line + max_lines)):
        parts.append(editor._doc.line_text(ln))
    if e_line - s_line < max_lines:
        parts.append(editor._doc.line_text(e_line)[:e_col])
    text = "\n".join(parts)
    if len(text) > MAX_CLIPBOARD:
        return text[:MAX_CLIPBOARD]
    return text


def delete_selection(editor, *, emit: bool = True) -> bool:
    if editor._read_only:
        return False
    if not has_selection(editor) and not editor._extra_cursors:
        return False
    spans = editor._multi_edit_spans()
    if spans:
        last_pos: tuple[int, int] | None = None
        for line, c0, c1 in spans:
            text = editor._doc.line_text(line)
            a = min(c0, len(text))
            b = min(max(c1, c0), len(text))
            if b > a:
                start = editor._doc.line_index().line_start(line) + editor._col_to_byte(line, a)
                end = editor._doc.line_index().line_start(line) + editor._col_to_byte(line, b)
                editor._delete_bytes_tracked(start, end - start)
            last_pos = (line, a)
        editor._extra_cursors.clear()
        editor._column_mode = False
        editor._column_anchor = None
        clear_selection(editor)
        if last_pos is not None:
            editor._cursor_line, editor._cursor_col = last_pos
        if emit:
            editor._emit_edit()
        return True
    if not has_selection(editor):
        return False
    s_line, s_col, e_line, e_col = editor_normalized_selection(editor)
    start = editor._doc.line_index().line_start(s_line) + editor._col_to_byte(s_line, s_col)
    end = editor._doc.line_index().line_start(e_line) + editor._col_to_byte(e_line, e_col)
    if end > start:
        editor._delete_bytes_tracked(start, end - start)
    editor._place_cursor_at(start)
    clear_selection(editor)
    if emit:
        editor._emit_edit()
    return True


def copy_selection(editor) -> None:
    text = selected_text(editor)
    if not text:
        text = editor._doc.line_text(editor._cursor_line)
    if text:
        QGuiApplication.clipboard().setText(text)


def cut_selection(editor) -> None:
    if editor._read_only:
        return
    if has_selection(editor):
        text = selected_text(editor)
        if text:
            QGuiApplication.clipboard().setText(text)
        delete_selection(editor)
        return
    line = editor._cursor_line
    total = editor._line_count()
    start = editor._doc.line_index().line_start(line)
    if line < total - 1:
        end = editor._doc.line_index().line_start(line + 1)
        text = editor._doc.line_text(line) + "\n"
    else:
        content = editor._doc.line_text(line)
        end = start + editor._col_to_byte(line, len(content))
        text = content
    if text:
        QGuiApplication.clipboard().setText(text)
    if end > start:
        editor._delete_bytes_tracked(start, end - start)
        editor._place_cursor_at(start)
        editor._emit_edit()


def paste_clipboard(editor) -> None:
    if editor._read_only:
        return
    text = QGuiApplication.clipboard().text()
    if not text:
        return
    if len(text) > MAX_CLIPBOARD:
        text = text[:MAX_CLIPBOARD]
    if has_selection(editor):
        delete_selection(editor, emit=False)
    editor._insert_at_cursor(text)


def select_all(editor) -> None:
    total = editor._line_count()
    if total <= 0:
        return
    editor._anchor_line = 0
    editor._anchor_col = 0
    last = total - 1
    editor._cursor_line = last
    editor._cursor_col = len(editor._doc.line_text(last))
    editor.cursorPositionChanged.emit()
    editor.viewport().update()


def begin_selection_if_needed(editor, shift: bool) -> None:
    if shift:
        if editor._anchor_line is None:
            editor._anchor_line = editor._cursor_line
            editor._anchor_col = editor._cursor_col
    else:
        clear_selection(editor)


def replace_word_on_line(editor, line: int, start_col: int, end_col: int, new_text: str) -> None:
    total = editor._line_count()
    if line < 0 or line >= total:
        return
    text = editor._doc.line_text(line)
    a = max(0, min(start_col, len(text)))
    b = max(a, min(end_col, len(text)))
    editor._extra_cursors.clear()
    editor._column_mode = False
    editor._column_anchor = None
    editor._cursor_line = line
    editor._anchor_line = line
    editor._anchor_col = a
    editor._cursor_col = b
    if b > a:
        delete_selection(editor, emit=False)
    editor._insert_at_cursor(new_text)
    editor._ensure_visible(line)
    editor.viewport().update()
