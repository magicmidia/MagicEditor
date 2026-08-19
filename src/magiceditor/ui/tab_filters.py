"""Tab-strip event filters extracted from TabManager (J1.5)."""

from __future__ import annotations

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QToolButton

from magiceditor.ui.icons import icon as make_icon


class CloseButtonFilter(QObject):
    """Swap close icon to white on hover (danger QSS paints red background)."""

    def __init__(self, owner) -> None:
        super().__init__(owner)
        self._owner = owner

    def eventFilter(self, obj: QObject | None, event: QEvent | None) -> bool:
        if obj is None or event is None or not isinstance(obj, QToolButton):
            return False
        if event.type() == QEvent.Type.Enter:
            obj.setIcon(make_icon("tab_close", "#FFFFFF"))
            return False
        if event.type() == QEvent.Type.Leave:
            obj.setIcon(make_icon("tab_close", self._owner._close_color))
            return False
        return False


class StripClickFilter(QObject):
    """Double-click empty tab strip → new document."""

    def __init__(self, owner) -> None:
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
