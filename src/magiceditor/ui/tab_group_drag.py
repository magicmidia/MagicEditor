"""Drag-to-group: passive tab-bar event filter + pure drop-target resolver.

The filter NEVER consumes events (always returns False), so the native
movable-tab reorder of ``QTabBar.setMovable(True)`` keeps working. It only
observes a left-button drag to paint a drop highlight on the target tab and,
on release, adds the dragged tab to that tab's group.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QEvent, QObject, QPoint, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication, QTabBar, QWidget

if TYPE_CHECKING:
    from magiceditor.ui.magic_tab_bar import MagicTabBar
    from magiceditor.ui.tab_group_anim import TabGroupAnimator
    from magiceditor.ui.tab_manager import TabManager


def drop_target_group(bar: QTabBar, pos: QPoint, dragged_index: int) -> str | None:
    """Group id of the tab under ``pos`` if dropping there joins that group.

    Returns None when ``pos`` is over empty strip area, over an ungrouped tab,
    or when the dragged tab already belongs to the target tab's group.
    """
    try:
        manager = bar.parentWidget()
    except (RuntimeError, AttributeError):
        return None
    if manager is None or not hasattr(manager, "group_of_index"):
        return None
    target = bar.tabAt(pos)
    if target < 0 or target == dragged_index:
        return None
    target_group = manager.group_of_index(target)
    if target_group is None:
        return None
    dragged_group = manager.group_of_index(dragged_index)
    if dragged_group is not None and dragged_group.group_id == target_group.group_id:
        return None
    return target_group.group_id


class TabGroupDropFilter(QObject):
    """Passive observer of tab drags that offers drop-to-group."""

    def __init__(self, manager: TabManager, animator: TabGroupAnimator | None = None) -> None:
        super().__init__(manager)
        self._manager = manager
        self._animator = animator
        self._press_pos: QPoint | None = None
        self._dragged_widget: QWidget | None = None
        self._dragging = False
        self._last_target_group: str | None = None

    def _reset(self) -> None:
        self._press_pos = None
        self._dragged_widget = None
        self._dragging = False
        self._last_target_group = None

    def _dragged_index(self) -> int:
        w = self._dragged_widget
        try:
            return self._manager.indexOf(w) if w is not None else -1
        except (RuntimeError, AttributeError):
            return -1

    def eventFilter(self, obj: QObject | None, event: QEvent | None) -> bool:
        try:
            bar = self._manager.tabBar()
        except (RuntimeError, AttributeError):
            return False
        if obj is not bar or event is None or not isinstance(event, QMouseEvent):
            return False
        etype = event.type()
        if etype == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                idx = bar.tabAt(event.position().toPoint())
                self._reset()
                if idx >= 0:
                    self._press_pos = event.position().toPoint()
                    self._dragged_widget = self._manager.widget(idx)
            return False
        if etype == QEvent.Type.MouseMove:
            if self._press_pos is None or self._dragged_widget is None:
                return False
            if not event.buttons() & Qt.MouseButton.LeftButton:
                return False
            pos = event.position().toPoint()
            if not self._dragging:
                if (pos - self._press_pos).manhattanLength() < QApplication.startDragDistance():
                    return False
                self._dragging = True
            self._update_highlight(bar, pos)
            return False
        if etype == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton and self._press_pos is not None:
                self._finish_drag(bar, event.position().toPoint())
            return False
        return False

    def _update_highlight(self, bar: MagicTabBar, pos: QPoint) -> None:
        gid = drop_target_group(bar, pos, self._dragged_index())
        if gid is None:
            bar.clear_drop_highlight()
            return
        self._last_target_group = gid
        target = bar.tabAt(pos)
        group = self._manager.group_of_index(target)
        if group is not None:
            bar.set_drop_highlight(target, group.color)

    def _finish_drag(self, bar: MagicTabBar, pos: QPoint) -> None:
        gid = drop_target_group(bar, pos, self._dragged_index()) if self._dragging else None
        if gid is None and self._dragging:
            gid = self._last_target_group
        widget = self._dragged_widget
        had_highlight = bar._drop_highlight_index >= 0
        self._reset()
        if gid is not None and widget is not None:
            final = self._manager.indexOf(widget)
            if final >= 0:
                self._manager.add_to_group(final, gid)
                if had_highlight and self._animator is not None:
                    self._animator.fade_highlight(bar)
                return
        bar.clear_drop_highlight()
