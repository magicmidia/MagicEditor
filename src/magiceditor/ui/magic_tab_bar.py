"""Tab bar chrome extracted from TabManager (J1.5)."""

from __future__ import annotations

from PyQt6.QtCore import QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent
from PyQt6.QtWidgets import QTabBar, QWidget


class MagicTabBar(QTabBar):
    """Tab bar: empty double-click, group color stripe, reliable movable drag."""

    empty_double_clicked = pyqtSignal()
    tab_context_menu = pyqtSignal(int, QPoint)  # index, global pos

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMovable(True)
        self.setExpanding(False)
        self.setElideMode(Qt.TextElideMode.ElideRight)
        self.setDrawBase(True)
        self.setUsesScrollButtons(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)
        self._group_colors: dict[int, str] = {}
        self._pref_height = 30
        self._pref_min_width = 72
        self._pref_max_width = 220

    def set_group_colors(self, mapping: dict[int, str]) -> None:
        self._group_colors = dict(mapping)
        self.update()

    def _on_context_menu(self, pos: QPoint) -> None:
        idx = self.tabAt(pos)
        self.tab_context_menu.emit(idx, self.mapToGlobal(pos))

    def mouseDoubleClickEvent(self, event: QMouseEvent | None) -> None:
        if event is not None and event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            if self._is_empty_hit(pos):
                self.empty_double_clicked.emit()
                event.accept()
                return
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event is not None and event.button() == Qt.MouseButton.MiddleButton:
            idx = self.tabAt(event.position().toPoint())
            if idx >= 0:
                parent = self.parentWidget()
                if hasattr(parent, '_middle_click_close') and parent._middle_click_close:
                    parent.tabCloseRequested.emit(idx)
                    event.accept()
                    return
        super().mousePressEvent(event)

    def paintEvent(self, event: QPaintEvent | None) -> None:
        super().paintEvent(event)
        if not self._group_colors:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        for index, hex_color in self._group_colors.items():
            if index < 0 or index >= self.count() or not self.isTabVisible(index):
                continue
            rect = self.tabRect(index)
            if rect.isEmpty():
                continue
            color = QColor(hex_color)
            stripe = QRect(rect.left() + 1, rect.top() + 4, 3, rect.height() - 8)
            painter.fillRect(stripe, color)
            painter.fillRect(rect.left(), rect.top(), rect.width(), 2, color)
        painter.end()

    def set_chrome_metrics(self, height: int, min_width: int, max_width: int) -> None:
        self._pref_height = max(22, min(40, height))
        self._pref_min_width = max(48, min(160, min_width))
        self._pref_max_width = max(self._pref_min_width, min(400, max_width))
        self.updateGeometry()
        self.update()

    def tabSizeHint(self, index: int) -> QSize:
        size = super().tabSizeHint(index)
        size.setHeight(self._pref_height)
        w = max(self._pref_min_width, min(self._pref_max_width, size.width()))
        size.setWidth(w)
        return size

    def _is_empty_hit(self, pos: QPoint) -> bool:
        if self.tabAt(pos) >= 0:
            return False
        if self.count() == 0:
            return True
        last = self.tabRect(self.count() - 1)
        if pos.x() > last.right() and 0 <= pos.y() <= max(last.height(), self.height()):
            return True
        first = self.tabRect(0)
        if pos.x() < first.left() and 0 <= pos.y() <= max(first.height(), self.height()):
            return True
        return 0 <= pos.y() <= self.height() and (
            pos.x() < 0 or pos.x() >= self.width() or self.tabAt(pos) < 0
        )

