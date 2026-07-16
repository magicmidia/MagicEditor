"""Virtual viewport editor — paints only visible lines from a piece table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QKeyEvent, QPainter, QPaintEvent, QWheelEvent
from PyQt6.QtWidgets import QAbstractScrollArea, QWidget

from magiceditor.core.syntax.rules import tokenize_line
from magiceditor.services.document import Document
from magiceditor.ui.fonts import editor_font

# kind -> (fg hex, bold) — match MagicHighlighter dark palette
_SYNTAX_PALETTE: dict[str, tuple[str, bool]] = {
    "keyword": ("#C792EA", True),
    "string": ("#C3E88D", False),
    "comment": ("#546E7A", False),
    "number": ("#F78C6C", False),
    "decorator": ("#82AAFF", False),
    "heading": ("#82AAFF", True),
    "code": ("#89DDFF", False),
    "link": ("#80CBC4", False),
}
_DEFAULT_FG = "#E2E8F0"
_FIND_BG = QColor(234, 179, 8, 90)
_MAX_REPLACE_ALL = 50_000
_MAX_UNDO = 500


@dataclass(slots=True)
class _EditOp:
    kind: Literal["insert", "delete"]
    offset: int
    data: bytes


class VirtualEditor(QAbstractScrollArea):
    """Huge-file viewer/editor surface.

    Does **not** load the full document into a ``QTextDocument``. Lines are
    fetched from the document piece table on paint. Editing mutates the
    piece table and keeps the line index incremental.
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
        self._language = "text"
        self._find_needle = ""
        self._find_case = False
        self._undo: list[_EditOp] = []
        self._redo: list[_EditOp] = []
        self._applying_history = False

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

    def set_language(self, language: str) -> None:
        if language == self._language:
            return
        self._language = language
        self.viewport().update()

    def language(self) -> str:
        return self._language

    def set_find_highlight(self, needle: str, *, case_sensitive: bool = False) -> None:
        self._find_needle = needle
        self._find_case = case_sensitive
        self.viewport().update()

    def goto_line(self, line: int, column: int = 0) -> None:
        """Move caret to 0-based line/column and scroll into view."""
        total = self._line_count()
        self._cursor_line = max(0, min(total - 1, line))
        text = self._doc.line_text(self._cursor_line)
        self._cursor_col = max(0, min(len(text), column))
        self._ensure_visible(self._cursor_line)
        self.cursorPositionChanged.emit()
        self.viewport().update()

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
        self.set_find_highlight(needle, case_sensitive=case_sensitive)
        enc = self._doc.encoding if self._doc.encoding != "utf-8-sig" else "utf-8"
        needle_b = needle.encode(enc, errors="replace")
        if not case_sensitive:
            needle_b = needle_b.lower()

        idx = self._doc.line_index()
        n_lines = idx.line_count
        if n_lines == 0:
            return False

        start_line = self._cursor_line
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
            if line == start_line and not backward:
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

    def replace_text(
        self,
        needle: str,
        replacement: str,
        *,
        case_sensitive: bool = False,
    ) -> bool:
        """Replace match at caret if it equals ``needle``, else find next and replace."""
        if not needle:
            return False
        self.set_find_highlight(needle, case_sensitive=case_sensitive)
        if not self._match_at_cursor(needle, case_sensitive=case_sensitive):
            if not self.find_text(needle, case_sensitive=case_sensitive, backward=False, wrap=True):
                return False
            if not self._match_at_cursor(needle, case_sensitive=case_sensitive):
                return False
        off = self._byte_offset_at_cursor()
        enc = self._doc.encoding if self._doc.encoding != "utf-8-sig" else "utf-8"
        needle_b = needle.encode(enc, errors="replace")
        repl_b = replacement.encode(enc, errors="replace")
        self._delete_bytes_tracked(off, len(needle_b))
        if repl_b:
            self._insert_bytes_tracked(off, repl_b)
        self._cursor_line = self._doc.line_index().offset_to_line(off + len(repl_b))
        line_start = self._doc.line_index().line_start(self._cursor_line)
        self._cursor_col = self._byte_to_col(self._cursor_line, off + len(repl_b) - line_start)
        self._emit_edit()
        return True

    def replace_all_text(
        self,
        needle: str,
        replacement: str,
        *,
        case_sensitive: bool = False,
        max_replacements: int = _MAX_REPLACE_ALL,
    ) -> int:
        """Replace all non-overlapping matches (line scan, reverse order)."""
        if not needle:
            return 0
        self.set_find_highlight(needle, case_sensitive=case_sensitive)
        enc = self._doc.encoding if self._doc.encoding != "utf-8-sig" else "utf-8"
        needle_b = needle.encode(enc, errors="replace")
        repl_b = replacement.encode(enc, errors="replace")
        needle_cmp = needle_b if case_sensitive else needle_b.lower()

        # Collect (byte_offset, length) from end so earlier offsets stay valid.
        matches: list[tuple[int, int]] = []
        idx = self._doc.line_index()
        for line in range(idx.line_count - 1, -1, -1):
            start = idx.line_start(line)
            length = idx.line_length(line)
            try:
                raw = self._doc.buffer.get_text(start, length)
            except IndexError:
                continue
            hay = raw if case_sensitive else raw.lower()
            pos = 0
            line_hits: list[tuple[int, int]] = []
            nlen = len(needle_cmp)
            if nlen == 0:
                break
            while True:
                found = hay.find(needle_cmp, pos)
                if found < 0:
                    break
                line_hits.append((start + found, len(needle_b)))
                pos = found + nlen
            matches.extend(reversed(line_hits))
            if len(matches) >= max_replacements:
                matches = matches[:max_replacements]
                break

        # Apply from highest offset first
        matches.sort(key=lambda m: m[0], reverse=True)
        count = 0
        for off, nlen in matches:
            self._delete_bytes_tracked(off, nlen)
            if repl_b:
                self._insert_bytes_tracked(off, repl_b)
            count += 1
        if count:
            self._cursor_line = min(self._cursor_line, self._line_count() - 1)
            self._cursor_col = min(
                self._cursor_col, len(self._doc.line_text(self._cursor_line))
            )
            self._emit_edit()
        return count

    def undo(self) -> None:
        if not self._undo:
            return
        op = self._undo.pop()
        self._applying_history = True
        try:
            if op.kind == "insert":
                self._doc.delete_bytes(op.offset, len(op.data))
                self._redo.append(op)
            else:
                self._doc.insert_bytes(op.offset, op.data)
                self._redo.append(op)
            self._place_cursor_at(op.offset)
            self._emit_edit(clear_redo=False)
        finally:
            self._applying_history = False

    def redo(self) -> None:
        if not self._redo:
            return
        op = self._redo.pop()
        self._applying_history = True
        try:
            if op.kind == "insert":
                self._doc.insert_bytes(op.offset, op.data)
                self._undo.append(op)
                self._place_cursor_at(op.offset + len(op.data))
            else:
                self._doc.delete_bytes(op.offset, len(op.data))
                self._undo.append(op)
                self._place_cursor_at(op.offset)
            self._emit_edit(clear_redo=False)
        finally:
            self._applying_history = False

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
        do_syntax = self._language not in {"", "text"}

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
            display = text.replace("\t", "    ")
            base_x = gutter + self._pad_x - h_off
            baseline = y + fm.ascent() + 1

            if self._find_needle:
                self._paint_find_hits(painter, text, base_x, y, lh, fm)

            if do_syntax and text and len(text) <= 8000:
                self._paint_syntax_line(painter, text, display, base_x, baseline, fm)
            else:
                painter.setPen(QColor(226, 232, 240))
                painter.drawText(base_x, baseline, display)

            if line == self._cursor_line:
                prefix = text[: self._cursor_col].replace("\t", "    ")
                cx = gutter + self._pad_x - h_off + fm.horizontalAdvance(prefix)
                painter.setPen(QColor(56, 189, 248))
                painter.drawLine(cx, y + 1, cx, y + lh - 2)

    def _paint_find_hits(
        self,
        painter: QPainter,
        text: str,
        base_x: int,
        y: int,
        lh: int,
        fm,
    ) -> None:
        needle = self._find_needle
        if not needle or not text:
            return
        hay = text if self._find_case else text.lower()
        n = needle if self._find_case else needle.lower()
        pos = 0
        while True:
            found = hay.find(n, pos)
            if found < 0:
                break
            prefix = text[:found].replace("\t", "    ")
            match = text[found : found + len(needle)].replace("\t", "    ")
            x0 = base_x + fm.horizontalAdvance(prefix)
            w = fm.horizontalAdvance(match)
            painter.fillRect(x0, y + 1, w, lh - 2, _FIND_BG)
            pos = found + max(1, len(n))

    def _paint_syntax_line(
        self,
        painter: QPainter,
        text: str,
        display: str,
        base_x: int,
        baseline: int,
        fm,
    ) -> None:
        """Paint a line with per-token colors (visible range only)."""
        spans = tokenize_line(text, self._language)
        claimed_end = 0
        x = base_x
        bold_font = QFont(self.font())
        bold_font.setBold(True)
        normal_font = self.font()

        def expand_slice(start: int, end: int) -> str:
            return text[start:end].replace("\t", "    ")

        for start, length, kind in spans:
            if start > claimed_end:
                gap = expand_slice(claimed_end, start)
                painter.setFont(normal_font)
                painter.setPen(QColor(_DEFAULT_FG))
                painter.drawText(x, baseline, gap)
                x += fm.horizontalAdvance(gap)
            chunk = expand_slice(start, start + length)
            color, bold = _SYNTAX_PALETTE.get(kind, (_DEFAULT_FG, False))
            painter.setFont(bold_font if bold else normal_font)
            painter.setPen(QColor(color))
            painter.drawText(x, baseline, chunk)
            x += fm.horizontalAdvance(chunk)
            claimed_end = start + length

        if claimed_end < len(text):
            tail = expand_slice(claimed_end, len(text))
            painter.setFont(normal_font)
            painter.setPen(QColor(_DEFAULT_FG))
            painter.drawText(x, baseline, tail)
        elif not spans:
            painter.setFont(normal_font)
            painter.setPen(QColor(_DEFAULT_FG))
            painter.drawText(base_x, baseline, display)

        painter.setFont(self.font())

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
        ctrl = bool(mod & Qt.KeyboardModifier.ControlModifier)

        if ctrl and key == Qt.Key.Key_Z and not (mod & Qt.KeyboardModifier.ShiftModifier):
            self.undo()
            event.accept()
            return
        shift = bool(mod & Qt.KeyboardModifier.ShiftModifier)
        if ctrl and (key == Qt.Key.Key_Y or (key == Qt.Key.Key_Z and shift)):
            self.redo()
            event.accept()
            return

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
        elif event.text() and not ctrl:
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

    # --- edits (piece table + incremental line index + undo) ----------

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

    def _match_at_cursor(self, needle: str, *, case_sensitive: bool) -> bool:
        text = self._doc.line_text(self._cursor_line)
        end = self._cursor_col + len(needle)
        if end > len(text):
            return False
        frag = text[self._cursor_col : end]
        if case_sensitive:
            return frag == needle
        return frag.lower() == needle.lower()

    def _push_undo(self, op: _EditOp) -> None:
        if self._applying_history:
            return
        self._undo.append(op)
        if len(self._undo) > _MAX_UNDO:
            self._undo = self._undo[-_MAX_UNDO:]
        self._redo.clear()

    def _insert_bytes_tracked(self, offset: int, data: bytes) -> None:
        if not data:
            return
        self._doc.insert_bytes(offset, data)
        self._push_undo(_EditOp("insert", offset, data))

    def _delete_bytes_tracked(self, offset: int, length: int) -> None:
        if length <= 0:
            return
        deleted = self._doc.buffer.get_text(offset, length)
        self._doc.delete_bytes(offset, length)
        self._push_undo(_EditOp("delete", offset, deleted))

    def _place_cursor_at(self, byte_off: int) -> None:
        byte_off = max(0, min(len(self._doc.buffer), byte_off))
        self._cursor_line = self._doc.line_index().offset_to_line(byte_off)
        line_start = self._doc.line_index().line_start(self._cursor_line)
        self._cursor_col = self._byte_to_col(self._cursor_line, byte_off - line_start)

    def _emit_edit(self, *, clear_redo: bool = True) -> None:
        if clear_redo and not self._applying_history:
            pass  # redo already cleared in _push_undo
        self._modified = True
        self._update_scrollbars()
        self.textChanged.emit()
        self.modificationChanged.emit(True)
        self.cursorPositionChanged.emit()
        self.viewport().update()

    def _insert_at_cursor(self, text: str) -> None:
        enc = self._doc.encoding if self._doc.encoding != "utf-8-sig" else "utf-8"
        data = text.encode(enc, errors="replace")
        off = self._byte_offset_at_cursor()
        self._insert_bytes_tracked(off, data)
        if b"\n" in data or b"\r" in data:
            self._cursor_line = self._doc.line_index().offset_to_line(off + len(data))
            line_start = self._doc.line_index().line_start(self._cursor_line)
            self._cursor_col = self._byte_to_col(self._cursor_line, off + len(data) - line_start)
        else:
            self._cursor_col += len(text)
        self._emit_edit()

    def _backspace(self) -> None:
        off = self._byte_offset_at_cursor()
        if off <= 0:
            return
        self._delete_bytes_tracked(off - 1, 1)
        self._place_cursor_at(off - 1)
        self._emit_edit()

    def _delete_forward(self) -> None:
        off = self._byte_offset_at_cursor()
        if off >= len(self._doc.buffer):
            return
        self._delete_bytes_tracked(off, 1)
        self._emit_edit()

    def cursor_line_col(self) -> tuple[int, int]:
        return self._cursor_line + 1, self._cursor_col + 1
