"""Key handling and indent for the virtual editor."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent

from magiceditor.core.indent import indent_unit, newline_auto_indent, unindent_prefix
from magiceditor.core.multi_cursor import word_at
from magiceditor.core.snippets import expand_snippet, match_trigger
from magiceditor.ui.virtual_cursors import backspace, delete_forward, editor_multi_spans
from magiceditor.ui.virtual_metrics import usable_line_slots


def newline_payload(line: str, col: int, language: str, *, spaces: bool, width: int) -> str:
    """Text inserted on Enter (newline + auto-indent)."""
    clipped = max(0, min(col, len(line)))
    before = line[:clipped]
    unit = indent_unit(spaces=spaces, width=width)
    return "\n" + newline_auto_indent(before, language, unit)


def indent_insert_text(*, spaces: bool, width: int) -> str:
    return indent_unit(spaces=spaces, width=width)


def intercept_tab_event(editor, event) -> bool:
    """True if Tab/Backtab was consumed (stay out of focus chain)."""
    if event is None:
        return False
    if getattr(event, "type", None) and event.type() != event.Type.KeyPress:
        return False
    if not isinstance(event, QKeyEvent):
        return False
    if event.key() not in {Qt.Key.Key_Tab, Qt.Key.Key_Backtab}:
        return False
    editor.keyPressEvent(event)
    return True


def handle_key_press(editor, event: QKeyEvent | None) -> bool:
    """Dispatch a key. True if handled (caller must not call super)."""
    if event is None:
        return True
    key = event.key()
    mod = event.modifiers()
    lines = editor._line_count()
    visible = usable_line_slots(editor)
    ctrl = bool(mod & Qt.KeyboardModifier.ControlModifier)
    shift = bool(mod & Qt.KeyboardModifier.ShiftModifier)

    if ctrl and key == Qt.Key.Key_Z and not shift:
        if not editor._read_only:
            editor.undo()
        event.accept()
        return True
    if ctrl and (key == Qt.Key.Key_Y or (key == Qt.Key.Key_Z and shift)):
        if not editor._read_only:
            editor.redo()
        event.accept()
        return True

    nav_keys = {
        Qt.Key.Key_Up,
        Qt.Key.Key_Down,
        Qt.Key.Key_PageUp,
        Qt.Key.Key_PageDown,
        Qt.Key.Key_Home,
        Qt.Key.Key_End,
        Qt.Key.Key_Left,
        Qt.Key.Key_Right,
    }
    if key in nav_keys:
        editor._begin_selection_if_needed(shift)

    # Read-only: navigation/selection allowed; every editing key is a no-op.
    if editor._read_only and key not in nav_keys:
        event.accept()
        return True

    if key == Qt.Key.Key_Up:
        editor._cursor_line = max(0, editor._cursor_line - 1)
    elif key == Qt.Key.Key_Down:
        editor._cursor_line = min(lines - 1, editor._cursor_line + 1)
    elif key == Qt.Key.Key_PageUp:
        editor._cursor_line = max(0, editor._cursor_line - visible)
    elif key == Qt.Key.Key_PageDown:
        editor._cursor_line = min(lines - 1, editor._cursor_line + visible)
    elif key == Qt.Key.Key_Home:
        editor._cursor_col = 0
    elif key == Qt.Key.Key_End:
        editor._cursor_col = len(editor._doc.line_text(editor._cursor_line))
    elif key == Qt.Key.Key_Left:
        editor._cursor_col = max(0, editor._cursor_col - 1)
    elif key == Qt.Key.Key_Right:
        editor._cursor_col = min(
            len(editor._doc.line_text(editor._cursor_line)), editor._cursor_col + 1
        )
    elif key == Qt.Key.Key_Backtab or (key == Qt.Key.Key_Tab and shift and not ctrl):
        unindent_line(editor)
        event.accept()
        editor.viewport().update()
        return True
    elif key == Qt.Key.Key_Tab and not ctrl:
        if try_snippet_or_complete(editor):
            event.accept()
            editor._ensure_visible(editor._cursor_line)
            editor._update_brace_match()
            editor.cursorPositionChanged.emit()
            editor.viewport().update()
            return True
        if editor.has_selection():
            indent_line(editor)
        else:
            editor._insert_at_cursor(
                indent_insert_text(spaces=editor._indent_with_spaces, width=editor._tab_width)
            )
        event.accept()
        editor.viewport().update()
        return True
    elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
        if editor_multi_spans(editor):
            if editor.has_selection() or editor._extra_cursors:
                editor._delete_selection(emit=False)
        elif editor.has_selection():
            editor._delete_selection(emit=False)
        editor._insert_at_cursor(newline_for_editor(editor))
    elif key == Qt.Key.Key_Backspace:
        backspace(editor)
    elif key == Qt.Key.Key_Delete:
        delete_forward(editor)
    elif event.text() and not ctrl:
        if editor_multi_spans(editor):
            editor._insert_at_cursor(event.text())
        else:
            if editor.has_selection():
                editor._delete_selection(emit=False)
            editor._insert_at_cursor(event.text())
        if editor._word_completion and event.text().isalnum():
            refresh_completion_candidates(editor)
    else:
        return False

    editor._ensure_visible(editor._cursor_line)
    editor._update_brace_match()
    editor.cursorPositionChanged.emit()
    editor.viewport().update()
    event.accept()
    return True


def newline_for_editor(editor) -> str:
    return newline_payload(
        editor._doc.line_text(editor._cursor_line),
        editor._cursor_col,
        editor._language,
        spaces=editor._indent_with_spaces,
        width=editor._tab_width,
    )


def indent_line(editor) -> None:
    unit = indent_unit(spaces=editor._indent_with_spaces, width=editor._tab_width)
    chunk = unit.encode("utf-8")
    if editor.has_selection():
        s_line, _sc, e_line, _ec = editor._normalized_selection()
        for line in range(s_line, e_line + 1):
            start = editor._doc.line_index().line_start(line)
            editor._insert_bytes_tracked(start, chunk)
        editor._cursor_col += len(unit)
    else:
        start = editor._doc.line_index().line_start(editor._cursor_line)
        editor._insert_bytes_tracked(start, chunk)
        editor._cursor_col += len(unit)
    editor._clear_selection()
    editor._emit_edit()


def unindent_line(editor) -> None:
    lines = [editor._cursor_line]
    if editor.has_selection():
        s_line, _sc, e_line, _ec = editor._normalized_selection()
        lines = list(range(s_line, e_line + 1))
    stripped = 0
    for line in lines:
        text = editor._doc.line_text(line)
        strip = unindent_prefix(text, editor._tab_width)
        if strip <= 0:
            continue
        start = editor._doc.line_index().line_start(line)
        editor._delete_bytes_tracked(start, editor._col_to_byte(line, strip))
        stripped = strip
    if not stripped:
        return
    editor._cursor_col = max(0, editor._cursor_col - stripped)
    editor._clear_selection()
    editor._emit_edit()


def try_snippet_or_complete(editor) -> bool:
    if editor.has_selection() or editor._extra_cursors:
        return False
    line_text = editor._doc.line_text(editor._cursor_line)
    col = editor._cursor_col
    i = col
    while i > 0 and (line_text[i - 1].isalnum() or line_text[i - 1] in {"_", "$"}):
        i -= 1
    prefix = line_text[i:col]
    if not prefix:
        return False
    sn = match_trigger(prefix, editor._language)
    if sn is not None and (prefix == sn.trigger or prefix.endswith(sn.trigger)):
        body, caret = expand_snippet(sn.body)
        start_col = i if prefix == sn.trigger else col - len(sn.trigger)
        start = editor._doc.line_index().line_start(editor._cursor_line) + editor._col_to_byte(
            editor._cursor_line, start_col
        )
        end = editor._doc.line_index().line_start(editor._cursor_line) + editor._col_to_byte(
            editor._cursor_line, col
        )
        if end > start:
            editor._delete_bytes_tracked(start, end - start)
        enc = editor._doc.encoding if editor._doc.encoding != "utf-8-sig" else "utf-8"
        data = body.encode(enc, errors="replace")
        editor._insert_bytes_tracked(start, data)
        editor._place_cursor_at(start + len(body[:caret].encode(enc, errors="replace")))
        editor._emit_edit()
        return True
    if editor._word_completion:
        return apply_word_completion(editor, prefix, i, col)
    return False


def refresh_completion_candidates(editor) -> None:
    line_text = editor._doc.line_text(editor._cursor_line)
    w = word_at([line_text], 0, editor._cursor_col)
    if w is None:
        editor._completion_candidates = []
        return
    word, _start, _end = w
    prefix = word
    if not prefix:
        editor._completion_candidates = []
        return
    total = editor._line_count()
    lo = max(0, editor._cursor_line - 200)
    hi = min(total, editor._cursor_line + 200)
    found: set[str] = set()
    for ln in range(lo, hi):
        t = editor._doc.line_text(ln)
        for part in t.replace(",", " ").replace(".", " ").split():
            token = "".join(ch for ch in part if ch.isalnum() or ch == "_")
            if len(token) > len(prefix) and token.startswith(prefix):
                found.add(token)
    editor._completion_candidates = sorted(found)[:40]
    editor._completion_index = 0


def apply_word_completion(editor, prefix: str, start_col: int, end_col: int) -> bool:
    refresh_completion_candidates(editor)
    if not editor._completion_candidates:
        return False
    choice = editor._completion_candidates[
        editor._completion_index % len(editor._completion_candidates)
    ]
    editor._completion_index += 1
    start = editor._doc.line_index().line_start(editor._cursor_line) + editor._col_to_byte(
        editor._cursor_line, start_col
    )
    end = editor._doc.line_index().line_start(editor._cursor_line) + editor._col_to_byte(
        editor._cursor_line, end_col
    )
    if end > start:
        editor._delete_bytes_tracked(start, end - start)
    enc = editor._doc.encoding if editor._doc.encoding != "utf-8-sig" else "utf-8"
    data = choice.encode(enc, errors="replace")
    editor._insert_bytes_tracked(start, data)
    editor._cursor_col = start_col + len(choice)
    editor._emit_edit()
    return True
