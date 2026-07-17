"""Tab widget with middle-click close."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QTabWidget, QWidget


class TabManager(QTabWidget):
    """Multi-document tab bar."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        self.setUsesScrollButtons(True)
        # Breathing room so the close button is not flush with the tab edge.
        bar = self.tabBar()
        bar.setExpanding(False)
        bar.setElideMode(Qt.TextElideMode.ElideRight)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event is not None and event.button() == Qt.MouseButton.MiddleButton:
            idx = self.tabBar().tabAt(event.pos())
            if idx >= 0:
                self.tabCloseRequested.emit(idx)
                return
        super().mousePressEvent(event)
