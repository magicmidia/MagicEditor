"""Mouse / hit-test / wheel for VirtualEditor (J1.1)."""

from __future__ import annotations

from PyQt6.QtCore import QEvent, QPoint, Qt
from PyQt6.QtGui import QContextMenuEvent, QWheelEvent


def hit_test(editor, pos: QPoint) -> tuple[int, int]:
    """Map viewport point to (doc_line, char_col)."""
    first = editor.verticalScrollBar().value()
    lh = editor._line_height
    gutter = editor._gutter_width if editor._show_line_numbers else 0
    fm = editor.fontMetrics()
    space_w = fm.horizontalAdvance(" ")
    h_off = 0 if editor._word_wrap else editor.horizontalScrollBar().value() * space_w
    x = pos.x() - gutter - editor._pad_x + h_off
    y = 0
    total = editor._line_count()
    line = first
    while line < total:
        try:
            text = editor._doc.line_text(line)
        except IndexError:
            text = ""
        rows = editor._wrap_display_rows(text)
        for d0, _d1, row in rows:
            if y <= pos.y() < y + lh:
                col_disp = 0
                acc = 0
                for ch in row:
                    w = fm.horizontalAdvance(ch)
                    if acc + w / 2 >= x:
                        break
                    acc += w
                    col_disp += 1
                target_disp = d0 + col_disp
                col = 0
                disp = 0
                for ch in text:
                    step = 4 if ch == "\t" else 1
                    if disp + step > target_disp:
                        break
                    disp += step
                    col += 1
                return line, col
            y += lh
        line += 1
    return max(0, total - 1), 0


def handle_wheel(editor, event: QWheelEvent | None) -> bool:
    if event is None:
        return False
    delta = event.angleDelta().y()
    step = -3 if delta > 0 else 3
    sb = editor.verticalScrollBar()
    sb.setValue(sb.value() + step)
    event.accept()
    return True


def handle_mouse_press(editor, event) -> bool:
    if event is None:
        return False
    if event.button() == Qt.MouseButton.RightButton:
        editor.setFocus(Qt.FocusReason.MouseFocusReason)
        global_pos = event.globalPosition().toPoint()
        editor._context_menu_from_mouse = True
        editor._emit_context_menu(global_pos)
        event.accept()
        return True
    if event.button() != Qt.MouseButton.LeftButton:
        return False
    pos: QPoint = event.position().toPoint()
    line, col = hit_test(editor, pos)
    shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
    alt = bool(event.modifiers() & Qt.KeyboardModifier.AltModifier)
    ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
    if alt:
        editor._column_mode = True
        editor._column_anchor = (line, col)
        editor._extra_cursors.clear()
        editor._anchor_line = line
        editor._anchor_col = col
        editor._cursor_line = line
        editor._cursor_col = col
        editor._selecting = True
    elif ctrl:
        editor._extra_cursors.append((line, col, col))
        editor._cursor_line = line
        editor._cursor_col = col
    elif shift:
        if editor._anchor_line is None:
            editor._anchor_line = editor._cursor_line
            editor._anchor_col = editor._cursor_col
        editor._cursor_line = line
        editor._cursor_col = col
    else:
        editor._column_mode = False
        editor._column_anchor = None
        editor._extra_cursors.clear()
        editor._anchor_line = line
        editor._anchor_col = col
        editor._cursor_line = line
        editor._cursor_col = col
    editor._selecting = True
    editor._update_brace_match()
    editor.cursorPositionChanged.emit()
    editor.viewport().update()
    editor.setFocus()
    event.accept()
    return True


def handle_mouse_move(editor, event) -> bool:
    if editor._selecting and event is not None and (event.buttons() & Qt.MouseButton.LeftButton):
        pos: QPoint = event.position().toPoint()
        line, col = hit_test(editor, pos)
        editor._cursor_line = line
        editor._cursor_col = col
        if editor._column_mode and editor._column_anchor is not None:
            editor._anchor_line = editor._column_anchor[0]
            editor._anchor_col = editor._column_anchor[1]
        editor.cursorPositionChanged.emit()
        editor.viewport().update()
        event.accept()
        return True
    return False


def handle_mouse_release(editor, event) -> bool:
    if event is not None and event.button() == Qt.MouseButton.LeftButton:
        editor._selecting = False
        if (
            editor._anchor_line is not None
            and editor._anchor_line == editor._cursor_line
            and editor._anchor_col == editor._cursor_col
        ):
            editor._clear_selection()
        event.accept()
        return True
    return False


def handle_context_menu(editor, event: QContextMenuEvent | None) -> bool:
    if event is None:
        return False
    if not editor._context_menu_enabled:
        event.ignore()
        return True
    if editor._context_menu_from_mouse:
        editor._context_menu_from_mouse = False
        event.accept()
        return True
    editor._emit_context_menu(event.globalPos())
    event.accept()
    return True


def handle_viewport_event(editor, event: QEvent | None) -> bool | None:
    """Return True/False if handled; None means fall through to super."""
    if event is None:
        return False
    et = event.type()
    if et == QEvent.Type.MouseButtonPress:
        editor.mousePressEvent(event)
        return event.isAccepted()
    if et == QEvent.Type.MouseMove:
        editor.mouseMoveEvent(event)
        return event.isAccepted()
    if et == QEvent.Type.MouseButtonRelease:
        editor.mouseReleaseEvent(event)
        return event.isAccepted()
    if et == QEvent.Type.ContextMenu:
        editor.contextMenuEvent(event)
        return True
    return None
