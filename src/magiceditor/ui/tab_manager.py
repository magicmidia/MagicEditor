"""Tab widget with middle-click close, drag-reorder, and empty double-click new."""

from __future__ import annotations

from PyQt6.QtCore import QEvent, QObject, QPoint, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QStyle, QTabBar, QTabWidget, QToolButton, QWidget

from magiceditor.ui.icons import icon as make_icon


class _MagicTabBar(QTabBar):
    """Tab bar: empty-space double-click, reliable movable drag."""

    empty_double_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMovable(True)
        self.setExpanding(False)
        self.setElideMode(Qt.TextElideMode.ElideRight)
        self.setDrawBase(True)
        self.setUsesScrollButtons(True)
        # Accept clicks on the free strip next to tabs (full width of bar).
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def mouseDoubleClickEvent(self, event: QMouseEvent | None) -> None:
        if event is not None and event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            if self._is_empty_hit(pos):
                self.empty_double_clicked.emit()
                event.accept()
                return
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        # Middle-click close on tab (bar receives the event more reliably than parent).
        if event is not None and event.button() == Qt.MouseButton.MiddleButton:
            idx = self.tabAt(event.position().toPoint())
            if idx >= 0:
                parent = self.parentWidget()
                if isinstance(parent, TabManager):
                    parent.tabCloseRequested.emit(idx)
                event.accept()
                return
        super().mousePressEvent(event)

    def _is_empty_hit(self, pos: QPoint) -> bool:
        """True when click is on free strip / padding, not on a tab body."""
        if self.tabAt(pos) >= 0:
            return False
        # Also treat space after the last tab as empty (Chrome / Notepad++ parity).
        if self.count() == 0:
            return True
        last = self.tabRect(self.count() - 1)
        if pos.x() > last.right() and 0 <= pos.y() <= max(last.height(), self.height()):
            return True
        # Left of first tab (padding)
        first = self.tabRect(0)
        if pos.x() < first.left() and 0 <= pos.y() <= max(first.height(), self.height()):
            return True
        # Between tabs shouldn't happen with tabAt, but keep fallback
        return 0 <= pos.y() <= self.height() and (
            pos.x() < 0 or pos.x() >= self.width() or self.tabAt(pos) < 0
        )


class _StripClickFilter(QObject):
    """Catch double-clicks on the tab strip area of QTabWidget (outside bar widget)."""

    def __init__(self, owner: TabManager) -> None:
        super().__init__(owner)
        self._owner = owner

    def eventFilter(self, obj: QObject | None, event: QEvent | None) -> bool:
        if event is None or obj is not self._owner:
            return False
        if event.type() != QEvent.Type.MouseButtonDblClick:
            return False
        if not isinstance(event, QMouseEvent):
            return False
        if event.button() != Qt.MouseButton.LeftButton:
            return False
        if self._owner._hit_empty_strip(event.position().toPoint()):
            self._owner.empty_area_double_clicked.emit()
            return True
        return False


class TabManager(QTabWidget):
    """Multi-document tab bar with close button, drag-reorder, empty double-click new."""

    empty_area_double_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # Custom close buttons — Fusion + empty QSS ::close-button hides default X.
        self.setTabsClosable(False)
        self.setDocumentMode(True)
        self.setUsesScrollButtons(True)
        self.setMovable(True)

        bar = _MagicTabBar(self)
        bar.empty_double_clicked.connect(self.empty_area_double_clicked.emit)
        self.setTabBar(bar)
        # CRITICAL: setTabBar replaces the bar — re-apply movable AFTER setTabBar.
        bar.setMovable(True)
        self.setMovable(True)

        self._close_color = "#94A3B8"
        self._strip_filter = _StripClickFilter(self)
        self.installEventFilter(self._strip_filter)

        # Corner «+» so new-tab is always one click away (in addition to double-click).
        self._new_tab_btn = QToolButton(self)
        self._new_tab_btn.setObjectName("tabNewButton")
        self._new_tab_btn.setAutoRaise(True)
        self._new_tab_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._new_tab_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._new_tab_btn.setFixedSize(22, 22)
        self._new_tab_btn.setIconSize(QSize(14, 14))
        self._new_tab_btn.setToolTip("Novo arquivo")
        self._new_tab_btn.clicked.connect(self.empty_area_double_clicked.emit)
        self.setCornerWidget(self._new_tab_btn, Qt.Corner.TopRightCorner)
        self._refresh_new_tab_icon()

    def set_close_icon_color(self, color: str) -> None:
        """Recolor tab close buttons and + (call when theme changes)."""
        self._close_color = color
        bar = self.tabBar()
        for i in range(bar.count()):
            btn = bar.tabButton(i, QTabBar.ButtonPosition.RightSide)
            if isinstance(btn, QToolButton):
                btn.setIcon(make_icon("tab_close", color))
        self._refresh_new_tab_icon()

    def _refresh_new_tab_icon(self) -> None:
        # Prefer a dedicated "new" icon; fall back to style standard icon.
        try:
            ic = make_icon("new", self._close_color)
            if not ic.isNull():
                self._new_tab_btn.setIcon(ic)
                return
        except Exception:
            pass
        style = self.style()
        if style is not None:
            self._new_tab_btn.setIcon(
                style.standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder)
            )

    def tabInserted(self, index: int) -> None:
        super().tabInserted(index)
        self._install_close_button(index)
        # Keep movable after structural changes (some styles reset flags).
        bar = self.tabBar()
        if not bar.isMovable():
            bar.setMovable(True)

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
        # Do not steal drag: only react to click, ignore drag start from button area.
        btn.setAttribute(Qt.WidgetAttribute.WA_LayoutUsesWidgetRect, True)
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

    def _hit_empty_strip(self, local: QPoint) -> bool:
        """Whether *local* (TabManager coords) is empty strip of the tab row."""
        bar = self.tabBar()
        strip_top = bar.y()
        strip_bottom = bar.y() + max(bar.height(), 28)
        if not (strip_top <= local.y() <= strip_bottom):
            return False
        # Map into bar; points to the right of bar still count as empty strip.
        bar_pos = bar.mapFrom(self, local)
        if bar.tabAt(bar_pos) >= 0:
            return False
        # If over the + corner button, let the button handle it.
        corner = self.cornerWidget(Qt.Corner.TopRightCorner)
        if corner is not None and corner.isVisible():
            cpos = corner.mapFrom(self, local)
            if corner.rect().contains(cpos):
                return False
        return True

    def mouseDoubleClickEvent(self, event: QMouseEvent | None) -> None:
        if (
            event is not None
            and event.button() == Qt.MouseButton.LeftButton
            and self._hit_empty_strip(event.position().toPoint())
        ):
            self.empty_area_double_clicked.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event is not None and event.button() == Qt.MouseButton.MiddleButton:
            bar = self.tabBar()
            bar_pos = bar.mapFrom(self, event.position().toPoint())
            idx = bar.tabAt(bar_pos)
            if idx >= 0:
                self.tabCloseRequested.emit(idx)
                return
        super().mousePressEvent(event)
