"""Mouse / hit-test / wheel for VirtualEditor (J1.1)."""

from __future__ import annotations

from PyQt6.QtCore import QEvent, QPoint, Qt, QTimer
from PyQt6.QtGui import QContextMenuEvent, QWheelEvent

from magiceditor.ui.virtual_metrics import scroll_origin


def hit_test(editor, pos: QPoint) -> tuple[int, int]:
    """Map viewport point to (doc_line, char_col) in O(1) or O(visible)."""
    first, skip = scroll_origin(editor)
    lh = max(1, int(getattr(editor, "_line_height", 18) or 18))
    gutter = editor._gutter_width if editor._show_line_numbers else 0
    fm = editor.fontMetrics()
    space_w = max(1, fm.horizontalAdvance(" "))
    h_off = 0 if editor._word_wrap else editor.horizontalScrollBar().value() * space_w
    x = pos.x() - gutter - editor._pad_x + h_off
    total = editor._line_count()
    if total <= 0:
        return 0, 0

    if not editor._word_wrap:
        rel_row = max(0, pos.y() // lh) if pos.y() >= 0 else 0
        line = min(total - 1, max(0, first + rel_row))
        try:
            text = editor._doc.line_text(line)
        except IndexError:
            return line, 0

        target_col = max(0, round(x / space_w)) if x > 0 else 0
        if "\t" not in text:
            col = min(len(text), target_col)
            return line, col

        disp = 0
        col = 0
        for ch in text:
            step = 4 if ch == "\t" else 1
            if disp + step > target_col:
                break
            disp += step
            col += 1
        return line, min(len(text), col)

    y = 0
    line = first
    view_h = editor.viewport().height()
    target_y = pos.y()

    while line < total and y <= max(view_h, target_y):
        try:
            text = editor._doc.line_text(line)
        except IndexError:
            text = ""
        rows = editor._wrap_display_rows(text)
        if skip and line == first:
            rows = rows[skip:]
        for d0, _d1, _row in rows:
            if y <= target_y < y + lh:
                target_col = max(0, round(x / space_w)) if x > 0 else 0
                target_disp = d0 + target_col
                disp = 0
                col = 0
                for ch in text:
                    step = 4 if ch == "\t" else 1
                    if disp + step > target_disp:
                        break
                    disp += step
                    col += 1
                return line, min(len(text), col)
            y += lh
        line += 1
    return min(total - 1, max(0, line - 1)), 0


def handle_wheel(editor, event: QWheelEvent | None) -> bool:
    if event is None:
        return False
    delta = event.angleDelta().y()
    ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
    if ctrl and getattr(editor, "_wheel_zoom", True) and delta:
        if delta > 0:
            editor.zoom_in_one()
        else:
            editor.zoom_out_one()
        event.accept()
        return True
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
        height = editor.viewport().height()
        if pos.y() < 0:
            dy = pos.y()
        elif pos.y() >= height:
            dy = pos.y() - (height - 1)
        else:
            dy = 0
        # Clamp into the viewport so hit_test stays O(visible) and the
        # selection cannot jump to the document end while auto-scrolling.
        clamped = QPoint(pos.x(), min(max(pos.y(), 0), max(0, height - 1)))
        editor._auto_scroll_pos = clamped
        editor._auto_scroll_dy = dy
        if dy:
            _auto_scroll_timer(editor).start()
        else:
            _stop_auto_scroll(editor)
        line, col = hit_test(editor, clamped)
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


def _auto_scroll_timer(editor) -> QTimer:
    timer = editor._auto_scroll_timer
    if timer is None:
        timer = QTimer(editor)
        timer.setInterval(30)
        timer.timeout.connect(lambda: _auto_scroll_tick(editor))
        editor._auto_scroll_timer = timer
    return timer


def _stop_auto_scroll(editor) -> None:
    editor._auto_scroll_dy = 0
    if editor._auto_scroll_timer is not None:
        editor._auto_scroll_timer.stop()


def _auto_scroll_tick(editor) -> None:
    dy = editor._auto_scroll_dy
    pos = editor._auto_scroll_pos
    if not editor._selecting or dy == 0 or pos is None:
        _stop_auto_scroll(editor)
        return
    lh = max(1, editor._line_height)
    lines = max(1, abs(dy) // lh)  # faster the further past the edge
    sb = editor.verticalScrollBar()
    sb.setValue(sb.value() + (lines if dy > 0 else -lines))
    line, col = hit_test(editor, pos)
    editor._cursor_line = line
    editor._cursor_col = col
    if editor._column_mode and editor._column_anchor is not None:
        editor._anchor_line = editor._column_anchor[0]
        editor._anchor_col = editor._column_anchor[1]
    editor.cursorPositionChanged.emit()
    editor.viewport().update()


def handle_mouse_release(editor, event) -> bool:
    if event is not None and event.button() == Qt.MouseButton.LeftButton:
        editor._selecting = False
        _stop_auto_scroll(editor)
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
