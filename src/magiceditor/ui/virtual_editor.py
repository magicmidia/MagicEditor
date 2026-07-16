"""Virtual viewport editor — paints only visible lines from a piece table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QKeyEvent, QPainter, QPaintEvent, QWheelEvent
from PyQt6.QtWidgets import QAbstractScrollArea, QWidget

from magiceditor.core.line_wrap import expand_tabs, wrap_ranges
from magiceditor.core.syntax.rules import tokenize_line
from magiceditor.core.text_match import (
    PatternError,
    compile_pattern,
    expand_replacement,
    find_all_matches,
    find_first,
    find_last_before,
)
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
        self._word_wrap = False
        self._bookmarks: set[int] = set()
        self._cursor_line = 0
        self._cursor_col = 0
        self._modified = False
        self._line_height = 18
        self._gutter_width = 56
        self._pad_x = 8
        self._language = "text"
        self._find_needle = ""
        self._find_case = False
        self._find_regex = False
        self._last_match_start_col = -1
        self._last_match_end_col = 0
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

    def set_find_highlight(
        self,
        needle: str,
        *,
        case_sensitive: bool = False,
        use_regex: bool = False,
    ) -> None:
        self._find_needle = needle
        self._find_case = case_sensitive
        self._find_regex = use_regex
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
        self._gutter_width = 56 if visible else 0
        self.viewport().update()

    def set_word_wrap(self, enabled: bool) -> None:
        self._word_wrap = enabled
        self._update_scrollbars()
        self.viewport().update()

    def toggle_bookmark(self) -> None:
        line = self._cursor_line
        if line in self._bookmarks:
            self._bookmarks.discard(line)
        else:
            self._bookmarks.add(line)
        self.viewport().update()

    def get_bookmarks(self) -> list[int]:
        return sorted(self._bookmarks)

    def set_bookmarks(self, lines: list[int] | set[int]) -> None:
        self._bookmarks = {int(x) for x in lines if int(x) >= 0}
        self.viewport().update()

    def next_bookmark(self) -> bool:
        if not self._bookmarks:
            return False
        after = sorted(b for b in self._bookmarks if b > self._cursor_line)
        target = after[0] if after else min(self._bookmarks)
        self.goto_line(target, 0)
        return True

    def prev_bookmark(self) -> bool:
        if not self._bookmarks:
            return False
        before = sorted(b for b in self._bookmarks if b < self._cursor_line)
        target = before[-1] if before else max(self._bookmarks)
        self.goto_line(target, 0)
        return True

    def has_bookmark(self, line: int) -> bool:
        return line in self._bookmarks

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
        use_regex: bool = False,
    ) -> bool:
        if not needle:
            return False
        try:
            pattern = compile_pattern(
                needle, case_sensitive=case_sensitive, use_regex=use_regex
            )
        except PatternError:
            return False
        self.set_find_highlight(needle, case_sensitive=case_sensitive, use_regex=use_regex)

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
                text = self._doc.line_text(line)
            except IndexError:
                continue
            if backward:
                before = self._cursor_col if line == start_line else len(text) + 1
                m = find_last_before(text, pattern, before=before)
            else:
                start_col = 0
                if line == start_line:
                    if self._cursor_col == self._last_match_start_col:
                        start_col = self._last_match_end_col
                    else:
                        start_col = self._cursor_col
                m = find_first(text, pattern, start=start_col)
            if m is None:
                continue
            self._cursor_line = line
            self._cursor_col = m.start()
            self._last_match_start_col = m.start()
            self._last_match_end_col = m.end()
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
        use_regex: bool = False,
    ) -> bool:
        """Replace match at caret if it matches ``needle``, else find next and replace."""
        if not needle:
            return False
        try:
            pattern = compile_pattern(
                needle, case_sensitive=case_sensitive, use_regex=use_regex
            )
        except PatternError:
            return False
        self.set_find_highlight(needle, case_sensitive=case_sensitive, use_regex=use_regex)

        m = self._match_at_cursor_re(pattern)
        if m is None:
            if not self.find_text(
                needle,
                case_sensitive=case_sensitive,
                backward=False,
                wrap=True,
                use_regex=use_regex,
            ):
                return False
            m = self._match_at_cursor_re(pattern)
            if m is None:
                return False

        repl_text = expand_replacement(m, replacement) if use_regex else replacement
        self._replace_char_span(self._cursor_line, m.start(), m.end(), repl_text)
        return True

    def replace_all_text(
        self,
        needle: str,
        replacement: str,
        *,
        case_sensitive: bool = False,
        use_regex: bool = False,
        max_replacements: int = _MAX_REPLACE_ALL,
    ) -> int:
        """Replace all non-overlapping matches (line scan, reverse order)."""
        if not needle:
            return 0
        try:
            pattern = compile_pattern(
                needle, case_sensitive=case_sensitive, use_regex=use_regex
            )
        except PatternError:
            return 0
        self.set_find_highlight(needle, case_sensitive=case_sensitive, use_regex=use_regex)

        # (line, start_col, end_col, expanded_repl) from end of file
        jobs: list[tuple[int, int, int, str]] = []
        idx = self._doc.line_index()
        for line in range(idx.line_count - 1, -1, -1):
            try:
                text = self._doc.line_text(line)
            except IndexError:
                continue
            matches = find_all_matches(text, pattern)
            for m in reversed(matches):
                repl = expand_replacement(m, replacement) if use_regex else replacement
                jobs.append((line, m.start(), m.end(), repl))
                if len(jobs) >= max_replacements:
                    break
            if len(jobs) >= max_replacements:
                break

        count = 0
        # Apply high line first, high col first (already reverse)
        for line, start_col, end_col, repl in jobs:
            # Re-fetch line text after prior edits on same line
            try:
                self._replace_char_span(line, start_col, end_col, repl, emit=False)
            except (IndexError, ValueError):
                continue
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
        if self._word_wrap:
            self.horizontalScrollBar().setRange(0, 0)
        else:
            self.horizontalScrollBar().setRange(0, 200)
            self.horizontalScrollBar().setPageStep(20)

    def _text_area_width(self) -> int:
        gutter = self._gutter_width if self._show_line_numbers else 0
        return max(40, self.viewport().width() - gutter - self._pad_x * 2)

    def _wrap_display_rows(self, text: str) -> list[tuple[int, int, str]]:
        """Return (disp_start, disp_end, row_text) for expanded display string."""
        display = expand_tabs(text)
        if not self._word_wrap:
            return [(0, len(display), display)]
        fm = self.fontMetrics()
        max_w = self._text_area_width()
        ranges = wrap_ranges(display, max_w, fm.horizontalAdvance)
        return [(a, b, display[a:b]) for a, b in ranges]

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
        space_w = fm.horizontalAdvance(" ")
        h_off = 0 if self._word_wrap else self.horizontalScrollBar().value() * space_w
        gutter = self._gutter_width if self._show_line_numbers else 0
        total = self._line_count()
        do_syntax = self._language not in {"", "text"} and not self._word_wrap
        view_h = self.viewport().height()

        if gutter:
            painter.fillRect(0, 0, gutter, view_h, QColor(127, 127, 127, 18))

        y = 0
        line = first
        while y < view_h and line < total:
            try:
                text = self._doc.line_text(line)
            except IndexError:
                text = ""
            rows = self._wrap_display_rows(text)
            row_h = lh * len(rows)
            if line == self._cursor_line:
                painter.fillRect(
                    gutter,
                    y,
                    self.viewport().width() - gutter,
                    row_h,
                    QColor(56, 189, 248, 28),
                )
            if gutter:
                if line in self._bookmarks:
                    painter.setBrush(QColor(56, 189, 248, 200))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(4, y + lh // 2 - 4, 8, 8)
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

            base_x = gutter + self._pad_x - h_off
            for ri, (d0, d1, row) in enumerate(rows):
                ry = y + ri * lh
                if ry > view_h:
                    break
                baseline = ry + fm.ascent() + 1
                if self._find_needle:
                    self._paint_find_hits_row(painter, text, d0, d1, base_x, ry, lh, fm)
                if do_syntax and text and len(text) <= 8000 and not self._word_wrap:
                    self._paint_syntax_line(painter, text, row, base_x, baseline, fm)
                else:
                    painter.setPen(QColor(226, 232, 240))
                    painter.drawText(base_x, baseline, row)

                if line == self._cursor_line:
                    caret_disp = len(expand_tabs(text[: self._cursor_col]))
                    if d0 <= caret_disp <= d1:
                        prefix = row[: caret_disp - d0]
                        cx = base_x + fm.horizontalAdvance(prefix)
                        painter.setPen(QColor(56, 189, 248))
                        painter.drawLine(cx, ry + 1, cx, ry + lh - 2)

            y += row_h
            line += 1

    def _paint_find_hits_row(
        self,
        painter: QPainter,
        text: str,
        d0: int,
        d1: int,
        base_x: int,
        y: int,
        lh: int,
        fm,
    ) -> None:
        needle = self._find_needle
        if not needle or not text:
            return
        try:
            pattern = compile_pattern(
                needle,
                case_sensitive=self._find_case,
                use_regex=self._find_regex,
            )
        except PatternError:
            return
        for m in find_all_matches(text, pattern):
            md0 = len(expand_tabs(text[: m.start()]))
            md1 = len(expand_tabs(text[: m.end()]))
            if md1 <= d0 or md0 >= d1:
                continue
            a = max(md0, d0) - d0
            b = min(md1, d1) - d0
            row = expand_tabs(text)[d0:d1]
            x0 = base_x + fm.horizontalAdvance(row[:a])
            w = fm.horizontalAdvance(row[a:b])
            painter.fillRect(x0, y + 1, max(1, w), lh - 2, _FIND_BG)

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
            line, col = self._hit_test(pos)
            self._cursor_line = line
            self._cursor_col = col
            self.cursorPositionChanged.emit()
            self.viewport().update()
            self.setFocus()
        super().mousePressEvent(event)

    def _hit_test(self, pos: QPoint) -> tuple[int, int]:
        """Map viewport point to (doc_line, char_col)."""
        first = self.verticalScrollBar().value()
        lh = self._line_height
        gutter = self._gutter_width if self._show_line_numbers else 0
        fm = self.fontMetrics()
        space_w = fm.horizontalAdvance(" ")
        h_off = 0 if self._word_wrap else self.horizontalScrollBar().value() * space_w
        x = pos.x() - gutter - self._pad_x + h_off
        y = 0
        total = self._line_count()
        line = first
        while line < total:
            try:
                text = self._doc.line_text(line)
            except IndexError:
                text = ""
            rows = self._wrap_display_rows(text)
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
                    # Map expanded display index back to text column
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

    def _match_at_cursor_re(self, pattern) -> object | None:
        """Return re.Match if a match starts at the caret column."""
        text = self._doc.line_text(self._cursor_line)
        m = pattern.match(text, self._cursor_col)
        return m

    def _replace_char_span(
        self,
        line: int,
        start_col: int,
        end_col: int,
        replacement: str,
        *,
        emit: bool = True,
    ) -> None:
        """Replace character range on a line via byte offsets."""
        enc = self._doc.encoding if self._doc.encoding != "utf-8-sig" else "utf-8"
        line_start = self._doc.line_index().line_start(line)
        off = line_start + self._col_to_byte(line, start_col)
        end_off = line_start + self._col_to_byte(line, end_col)
        if end_off > off:
            self._delete_bytes_tracked(off, end_off - off)
        repl_b = replacement.encode(enc, errors="replace")
        if repl_b:
            self._insert_bytes_tracked(off, repl_b)
        if emit:
            self._place_cursor_at(off + len(repl_b))
            self._last_match_start_col = -1
            self._last_match_end_col = 0
            self._emit_edit()

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
