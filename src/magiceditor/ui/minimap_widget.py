"""Lightweight minimap for small/medium buffers (degrades on huge files)."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPaintEvent
from PyQt6.QtWidgets import QWidget


class MinimapWidget(QWidget):
    """Shows a density strip of the document; click jumps to ratio."""

    jump_ratio = pyqtSignal(float)  # 0.0-1.0

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(64)
        self._lines: list[str] = []
        self._viewport_start = 0.0
        self._viewport_end = 0.1
        self._enabled = True
        self._bg = QColor(20, 20, 20)
        self._fg = QColor(180, 180, 180, 120)
        self._view = QColor(255, 215, 0, 40)

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self.setVisible(enabled)
        self.update()

    def set_document_lines(self, lines: list[str], *, max_lines: int = 4000) -> None:
        if len(lines) > max_lines:
            # sample
            step = max(1, len(lines) // max_lines)
            self._lines = lines[::step][:max_lines]
        else:
            self._lines = list(lines)
        self.update()

    def set_viewport_ratio(self, start: float, end: float) -> None:
        self._viewport_start = max(0.0, min(1.0, start))
        self._viewport_end = max(self._viewport_start, min(1.0, end))
        self.update()

    def paintEvent(self, event: QPaintEvent | None) -> None:
        if not self._enabled:
            return
        p = QPainter(self)
        p.fillRect(self.rect(), self._bg)
        h = max(1, self.height())
        w = self.width()
        n = max(1, len(self._lines))
        for i, line in enumerate(self._lines):
            y = int(i * h / n)
            density = min(1.0, len(line.strip()) / 80.0)
            if density <= 0:
                continue
            p.fillRect(4, y, int((w - 8) * density), 1, self._fg)
        # viewport
        y0 = int(self._viewport_start * h)
        y1 = int(self._viewport_end * h)
        p.fillRect(0, y0, w, max(2, y1 - y0), self._view)
        p.end()

    def mousePressEvent(self, event) -> None:
        if event is None or not self._enabled:
            return
        ratio = event.position().y() / max(1, self.height())
        self.jump_ratio.emit(max(0.0, min(1.0, ratio)))
