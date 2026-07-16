"""Modern text editor with line-number gutter and current-line highlight."""

from __future__ import annotations

from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import QColor, QPainter, QTextCharFormat, QTextCursor, QTextFormat
from PyQt6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget

from magiceditor.ui.fonts import editor_font


class _LineNumberArea(QWidget):
    def __init__(self, editor: TextEditor) -> None:
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:
        self._editor.paint_line_numbers(event)


class TextEditor(QPlainTextEdit):
    """Primary editing surface with gutter, highlight, and zoom."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._line_numbers = _LineNumberArea(self)
        self._show_line_numbers = True
        self._highlight_current = True
        self._bookmarks: set[int] = set()

        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setCenterOnScroll(False)
        self.setFont(editor_font(12))
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(" "))

        self.blockCountChanged.connect(self._update_line_number_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)

        self._update_line_number_width(0)
        self._highlight_current_line()

    def line_number_area_width(self) -> int:
        if not self._show_line_numbers:
            return 0
        digits = max(2, len(str(max(1, self.blockCount()))))
        return 18 + self.fontMetrics().horizontalAdvance("9") * digits

    def set_line_numbers_visible(self, visible: bool) -> None:
        self._show_line_numbers = visible
        self._update_line_number_width(0)
        self._line_numbers.setVisible(visible)

    def set_word_wrap(self, enabled: bool) -> None:
        mode = (
            QPlainTextEdit.LineWrapMode.WidgetWidth
            if enabled
            else QPlainTextEdit.LineWrapMode.NoWrap
        )
        self.setLineWrapMode(mode)

    def toggle_bookmark(self) -> None:
        bn = self.textCursor().blockNumber()
        if bn in self._bookmarks:
            self._bookmarks.discard(bn)
        else:
            self._bookmarks.add(bn)
        self._line_numbers.update()

    def get_bookmarks(self) -> list[int]:
        return sorted(self._bookmarks)

    def set_bookmarks(self, lines: list[int] | set[int]) -> None:
        self._bookmarks = {int(x) for x in lines if int(x) >= 0}
        self._line_numbers.update()

    def next_bookmark(self) -> bool:
        if not self._bookmarks:
            return False
        cur = self.textCursor().blockNumber()
        after = sorted(b for b in self._bookmarks if b > cur)
        target = after[0] if after else min(self._bookmarks)
        return self._goto_block(target)

    def prev_bookmark(self) -> bool:
        if not self._bookmarks:
            return False
        cur = self.textCursor().blockNumber()
        before = sorted(b for b in self._bookmarks if b < cur)
        target = before[-1] if before else max(self._bookmarks)
        return self._goto_block(target)

    def _goto_block(self, block_number: int) -> bool:
        block = self.document().findBlockByNumber(block_number)
        if not block.isValid():
            return False
        cursor = QTextCursor(block)
        self.setTextCursor(cursor)
        self.centerCursor()
        self.setFocus()
        return True

    def zoom_in_one(self) -> None:
        self.zoomIn(1)

    def zoom_out_one(self) -> None:
        self.zoomOut(1)

    def reset_zoom(self) -> None:
        self.setFont(editor_font(12))
        self._update_line_number_width(0)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_numbers.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def paint_line_numbers(self, event) -> None:
        painter = QPainter(self._line_numbers)
        painter.fillRect(event.rect(), QColor(127, 127, 127, 18))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        current = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                if block_number in self._bookmarks:
                    painter.setBrush(QColor(56, 189, 248, 200))
                    painter.setPen(Qt.PenStyle.NoPen)
                    cy = top + self.fontMetrics().height() // 2 - 4
                    painter.drawEllipse(3, cy, 8, 8)
                number = str(block_number + 1)
                if block_number == current:
                    painter.setPen(QColor(148, 163, 184, 230))
                else:
                    painter.setPen(QColor(148, 163, 184, 140))
                painter.drawText(
                    0,
                    top,
                    self._line_numbers.width() - 8,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    number,
                )
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def _update_line_number_width(self, _count: int) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self._line_numbers.scroll(0, dy)
        else:
            self._line_numbers.update(0, rect.y(), self._line_numbers.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_width(0)

    def _highlight_current_line(self) -> None:
        if not self._highlight_current or self.isReadOnly():
            self.setExtraSelections([])
            return
        selection = QTextEdit.ExtraSelection()
        fmt = QTextCharFormat()
        # Gold line highlight (Luminous Void); still readable on other themes
        fmt.setBackground(QColor(255, 215, 0, 28))
        fmt.setProperty(QTextFormat.Property.FullWidthSelection, True)
        selection.format = fmt
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        self.setExtraSelections([selection])
