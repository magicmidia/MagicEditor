"""Virtual viewport editor — paints only visible lines from a piece table."""

from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QKeyEvent, QPainter, QPaintEvent, QWheelEvent
from PyQt6.QtWidgets import QAbstractScrollArea, QWidget

from magiceditor.services.document import Document
from magiceditor.ui.fonts import editor_font


class VirtualEditor(QAbstractScrollArea):
    """Huge-file viewer/editor surface.

    Does **not** load the full document into a ``QTextDocument``. Lines are
    fetched from the document piece table on paint. Editing is limited
    (navigation + find); typing inserts into the piece table at the caret.
    """

    cursorPositionChanged = pyqtSignal()
    textChanged = pyqtSignal()
    modificationChanged = pyqtSignal(bool)

    def __init__(self, document: Document, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._doc = document
        self._show_line_numbers = True
        self._cursor_line = 0
        self._cursor_col = 0
        self._modified = False
        self._line_height = 18
        self._gutter_width = 48
        self._pad_x = 8

        self.setFont(editor_font(12))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFrameShape(self.Shape.NoFrame)
        self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        self._recalc_metrics()
        self._update_scrollbars()

    # --- public API (parity helpers for EditorTab / dialogs) ------------

    def document_model(self) -> Document:
        return self._doc

    def is_huge_mode(self) -> bool:
        return True

    def toPlainText(self) -> str:
        # Avoid materializing multi-GB strings casually.
        limit = 2 * 1024 * 1024
        raw = self._doc.buffer.get_text(0, min(len(self._doc.buffer), limit))
        enc = self._doc.encoding if self._doc.encoding != "utf-8-sig" else "utf-8"
        text = raw.decode(enc, errors="replace")
        if len(self._doc.buffer) > limit:
            text += "\n\n… [truncated for export — open smaller range or use external tools]"
        return text

    def set_line_numbers_visible(self, visible: bool) -> None:
        self._show_line_numbers = visible
        self._gutter_width = 48 if visible else 0
        self.viewport().update()

    def set_word_wrap(self, _enabled: bool) -> None:
        # Soft wrap not implemented in virtual mode (horizontal scroll only).
        pass

    def zoom_in_one(self) -> None:
        f = self.font()
        f.setPointSize(min(48, f.pointSize() + 1))
        self.setFont(f)
        self._recalc_metrics()
        self.viewport().update()

    def zoom_out_one(self) -> None:
        f = self.font()
        f.setPointSize(max(8, f.pointSize() - 1))
        self.setFont(f)
        self._recalc_metrics()
        self.viewport().update()

    def reset_zoom(self) -> None:
        self.setFont(editor_font(12))
        self._recalc_metrics()
        self.viewport().update()

    def find_text(
        self,
        needle: str,
        *,
        case_sensitive: bool = False,
        backward: bool = False,
        wrap: bool = True,
    ) -> bool:
        if not needle:
            return False
        enc = self._doc.encoding if self._doc.encoding != "utf-8-sig" else "utf-8"
        needle_b = needle.encode(enc, errors="replace")
        if not case_sensitive:
            needle_b = needle_b.lower()

        idx = self._doc.line_index()
        n_lines = idx.line_count
        if n_lines == 0:
            return False

        start_line = self._cursor_line
        order: list[int]
        if backward:
            order = list(range(start_line, -1, -1)) + (
                list(range(n_lines - 1, start_line, -1)) if wrap else []
            )
        else:
            order = list(range(start_line, n_lines)) + (list(range(0, start_line)) if wrap else [])

        for line in order:
            try:
                raw = self._doc.buffer.get_text(idx.line_start(line), idx.line_length(line))
            except IndexError:
                continue
            hay = raw if case_sensitive else raw.lower()
            pos = hay.find(needle_b)
            if pos < 0:
                continue
            # Skip current caret match when searching forward from same line
            if line == start_line and not backward:
                # find next occurrence after caret
                col_bytes = self._col_to_byte(line, self._cursor_col)
                pos = hay.find(needle_b, col_bytes + (1 if col_bytes < len(hay) else 0))
                if pos < 0:
                    continue
            self._cursor_line = line
            self._cursor_col = self._byte_to_col(line, pos)
            self._ensure_visible(line)
            self.cursorPositionChanged.emit()
            self.viewport().update()
            return True
        return False

    def centerCursor(self) -> None:
        self._ensure_visible(self._cursor_line)

    # --- metrics / scroll ---------------------------------------------

    def _recalc_metrics(self) -> None:
        self._line_height = max(14, self.fontMetrics().height() + 2)
        self._update_scrollbars()

    def _line_count(self) -> int:
        return max(1, self._doc.line_index().line_count)

    def _update_scrollbars(self) -> None:
        lines = self._line_count()
        visible = max(1, self.viewport().height() // self._line_height)
        self.verticalScrollBar().setRange(0, max(0, lines - 1))
        self.verticalScrollBar().setPageStep(visible)
        self.horizontalScrollBar().setRange(0, 200)
        self.horizontalScrollBar().setPageStep(20)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_scrollbars()

    def scrollContentsBy(self, dx: int, dy: int) -> None:
        self.viewport().scroll(dx, dy)
        self.viewport().update()

    def _ensure_visible(self, line: int) -> None:
        first = self.verticalScrollBar().value()
        visible = max(1, self.viewport().height() // self._line_height)
        if line < first:
            self.verticalScrollBar().setValue(line)
        elif line >= first + visible:
            self.verticalScrollBar().setValue(line - visible + 1)

    # --- paint --------------------------------------------------------

    def paintEvent(self, event: QPaintEvent | None) -> None:
        painter = QPainter(self.viewport())
        painter.fillRect(self.viewport().rect(), QColor(15, 23, 42))
        painter.setFont(self.font())
        fm = self.fontMetrics()
        lh = self._line_height
        first = self.verticalScrollBar().value()
        h_off = self.horizontalScrollBar().value() * fm.horizontalAdvance(" ")
        visible = self.viewport().height() // lh + 2
        gutter = self._gutter_width if self._show_line_numbers else 0
        total = self._line_count()

        if gutter:
            painter.fillRect(0, 0, gutter, self.viewport().height(), QColor(127, 127, 127, 18))

        for i in range(visible):
            line = first + i
            if line >= total:
                break
            y = i * lh
            if line == self._cursor_line:
                painter.fillRect(
                    gutter,
                    y,
                    self.viewport().width() - gutter,
                    lh,
                    QColor(56, 189, 248, 28),
                )
            if gutter:
                num = str(line + 1)
                painter.setPen(QColor(148, 163, 184, 230 if line == self._cursor_line else 140))
                painter.drawText(
                    0,
                    y,
                    gutter - 8,
                    lh,
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    num,
                )
            try:
                text = self._doc.line_text(line)
            except IndexError:
                text = ""
            painter.setPen(QColor(226, 232, 240))
            painter.drawText(
                gutter + self._pad_x - h_off,
                y + fm.ascent() + 1,
                text.replace("\t", "    "),
            )
            if line == self._cursor_line:
                prefix = text[: self._cursor_col].replace("\t", "    ")
                cx = gutter + self._pad_x - h_off + fm.horizontalAdvance(prefix)
                painter.setPen(QColor(56, 189, 248))
                painter.drawLine(cx, y + 1, cx, y + lh - 2)

    # --- input --------------------------------------------------------

    def wheelEvent(self, event: QWheelEvent | None) -> None:
        if event is None:
            return
        delta = event.angleDelta().y()
        step = -3 if delta > 0 else 3
        sb = self.verticalScrollBar()
        sb.setValue(sb.value() + step)
        event.accept()

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        if event is None:
            return
        key = event.key()
        mod = event.modifiers()
        lines = self._line_count()
        visible = max(1, self.viewport().height() // self._line_height)

        if key == Qt.Key.Key_Up:
            self._cursor_line = max(0, self._cursor_line - 1)
        elif key == Qt.Key.Key_Down:
            self._cursor_line = min(lines - 1, self._cursor_line + 1)
        elif key == Qt.Key.Key_PageUp:
            self._cursor_line = max(0, self._cursor_line - visible)
        elif key == Qt.Key.Key_PageDown:
            self._cursor_line = min(lines - 1, self._cursor_line + visible)
        elif key == Qt.Key.Key_Home:
            self._cursor_col = 0
        elif key == Qt.Key.Key_End:
            self._cursor_col = len(self._doc.line_text(self._cursor_line))
        elif key == Qt.Key.Key_Left:
            self._cursor_col = max(0, self._cursor_col - 1)
        elif key == Qt.Key.Key_Right:
            self._cursor_col = min(
                len(self._doc.line_text(self._cursor_line)), self._cursor_col + 1
            )
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._insert_at_cursor("\n")
        elif key == Qt.Key.Key_Backspace:
            self._backspace()
        elif key == Qt.Key.Key_Delete:
            self._delete_forward()
        elif event.text() and not (mod & Qt.KeyboardModifier.ControlModifier):
            self._insert_at_cursor(event.text())
        else:
            super().keyPressEvent(event)
            return

        self._ensure_visible(self._cursor_line)
        self.cursorPositionChanged.emit()
        self.viewport().update()
        event.accept()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            pos: QPoint = event.position().toPoint()
            first = self.verticalScrollBar().value()
            line = first + pos.y() // self._line_height
            line = max(0, min(self._line_count() - 1, line))
            gutter = self._gutter_width if self._show_line_numbers else 0
            x = pos.x() - gutter - self._pad_x
            text = self._doc.line_text(line)
            fm = self.fontMetrics()
            col = 0
            acc = 0
            for ch in text:
                w = fm.horizontalAdvance(ch if ch != "\t" else "    ")
                if acc + w / 2 >= x:
                    break
                acc += w
                col += 1
            self._cursor_line = line
            self._cursor_col = col
            self.cursorPositionChanged.emit()
            self.viewport().update()
            self.setFocus()
        super().mousePressEvent(event)

    # --- edits (piece table) ------------------------------------------

    def _byte_offset_at_cursor(self) -> int:
        idx = self._doc.line_index()
        start = idx.line_start(self._cursor_line)
        return start + self._col_to_byte(self._cursor_line, self._cursor_col)

    def _col_to_byte(self, line: int, col: int) -> int:
        text = self._doc.line_text(line)
        prefix = text[:col]
        enc = self._doc.encoding if self._doc.encoding != "utf-8-sig" else "utf-8"
        return len(prefix.encode(enc, errors="replace"))

    def _byte_to_col(self, line: int, byte_off: int) -> int:
        text = self._doc.line_text(line)
        enc = self._doc.encoding if self._doc.encoding != "utf-8-sig" else "utf-8"
        raw = text.encode(enc, errors="replace")
        # walk chars until bytes consumed
        used = 0
        col = 0
        for ch in text:
            b = ch.encode(enc, errors="replace")
            if used + len(b) > byte_off:
                break
            used += len(b)
            col += 1
            if used >= len(raw):
                break
        return col

    def _insert_at_cursor(self, text: str) -> None:
        enc = self._doc.encoding if self._doc.encoding != "utf-8-sig" else "utf-8"
        data = text.encode(enc, errors="replace")
        off = self._byte_offset_at_cursor()
        self._doc.buffer.insert(off, data)
        self._doc.mark_modified()
        self._modified = True
        # rebuild line index (acceptable until incremental index lands)
        self._doc._line_index = None
        if "\n" in text or "\r" in text:
            self._cursor_line = self._doc.line_index().offset_to_line(off + len(data))
            line_start = self._doc.line_index().line_start(self._cursor_line)
            self._cursor_col = self._byte_to_col(self._cursor_line, off + len(data) - line_start)
        else:
            self._cursor_col += len(text)
        self._update_scrollbars()
        self.textChanged.emit()
        self.modificationChanged.emit(True)
        self.viewport().update()

    def _backspace(self) -> None:
        off = self._byte_offset_at_cursor()
        if off <= 0:
            return
        self._doc.buffer.delete(off - 1, 1)
        self._doc.mark_modified()
        self._doc._line_index = None
        self._modified = True
        new_off = off - 1
        self._cursor_line = self._doc.line_index().offset_to_line(new_off)
        line_start = self._doc.line_index().line_start(self._cursor_line)
        self._cursor_col = self._byte_to_col(self._cursor_line, new_off - line_start)
        self._update_scrollbars()
        self.textChanged.emit()
        self.modificationChanged.emit(True)
        self.viewport().update()

    def _delete_forward(self) -> None:
        off = self._byte_offset_at_cursor()
        if off >= len(self._doc.buffer):
            return
        self._doc.buffer.delete(off, 1)
        self._doc.mark_modified()
        self._doc._line_index = None
        self._modified = True
        self._update_scrollbars()
        self.textChanged.emit()
        self.modificationChanged.emit(True)
        self.viewport().update()

    def cursor_line_col(self) -> tuple[int, int]:
        return self._cursor_line + 1, self._cursor_col + 1
