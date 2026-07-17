"""Tab widget with middle-click close and explicit close buttons."""

from __future__ import annotations

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QTabBar, QTabWidget, QToolButton, QWidget

from magiceditor.ui.icons import icon as make_icon


class TabManager(QTabWidget):
    """Multi-document tab bar with a reliable × close control."""

    empty_area_double_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # We install our own close buttons — QSS on QTabBar::close-button
        # without an image hides Fusion's default glyph entirely.
        self.setTabsClosable(False)
        self.setMovable(True)
        self.setDocumentMode(True)
        self.setUsesScrollButtons(True)
        bar = self.tabBar()
        bar.setExpanding(False)
        bar.setElideMode(Qt.TextElideMode.ElideRight)
        self._close_color = "#94A3B8"

    def set_close_icon_color(self, color: str) -> None:
        """Recolor all tab close buttons (call when theme changes)."""
        self._close_color = color
        bar = self.tabBar()
        for i in range(bar.count()):
            btn = bar.tabButton(i, QTabBar.ButtonPosition.RightSide)
            if isinstance(btn, QToolButton):
                btn.setIcon(make_icon("tab_close", color))

    def tabInserted(self, index: int) -> None:
        super().tabInserted(index)
        self._install_close_button(index)

    def _install_close_button(self, index: int) -> None:
        bar = self.tabBar()
        btn = QToolButton(self)
        btn.setObjectName("tabCloseButton")
        btn.setAutoRaise(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.setFixedSize(18, 18)
        btn.setIconSize(QSize(12, 12))
        btn.setIcon(make_icon("tab_close", self._close_color))
        btn.setToolTip("Fechar")
        btn.clicked.connect(self._on_close_clicked)
        bar.setTabButton(index, QTabBar.ButtonPosition.RightSide, btn)

    def _on_close_clicked(self) -> None:
        sender = self.sender()
        if not isinstance(sender, QToolButton):
            return
        bar = self.tabBar()
        for i in range(bar.count()):
            if bar.tabButton(i, QTabBar.ButtonPosition.RightSide) is sender:
                self.tabCloseRequested.emit(i)
                return

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event is not None and event.button() == Qt.MouseButton.MiddleButton:
            idx = self.tabBar().tabAt(event.pos())
            if idx >= 0:
                self.tabCloseRequested.emit(idx)
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent | None) -> None:
        if event is not None and event.button() == Qt.MouseButton.LeftButton:
            # Double-click empty tab bar → new document (Notepad++ parity)
            if self.tabBar().tabAt(event.pos()) < 0:
                self.empty_area_double_clicked.emit()
                event.accept()
                return
        super().mouseDoubleClickEvent(event)
