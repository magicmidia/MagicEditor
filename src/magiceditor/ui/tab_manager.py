"""Tab widget: scroll, close danger hover, Chrome-style groups, empty double-click."""

from __future__ import annotations

from PyQt6.QtCore import QPoint, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QStyle,
    QTabBar,
    QTabWidget,
    QToolButton,
    QWidget,
)

from magiceditor.ui.editor_tab import EditorTab
from magiceditor.ui.icons import icon as make_icon
from magiceditor.ui.magic_tab_bar import MagicTabBar
from magiceditor.ui.tab_filters import CloseButtonFilter, StripClickFilter
from magiceditor.ui.tab_group_actions import show_tab_context_menu
from magiceditor.ui.tab_group_anim import TabGroupAnimator
from magiceditor.ui.tab_group_drag import TabGroupDropFilter
from magiceditor.ui.tab_groups import TabGroup, TabGroupStore

_MagicTabBar = MagicTabBar
_CloseButtonFilter = CloseButtonFilter
_StripClickFilter = StripClickFilter


class TabManager(QTabWidget):
    """Multi-document tab bar with close, scroll, groups, drag-reorder."""

    empty_area_double_clicked = pyqtSignal()
    groups_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTabsClosable(False)
        self.setDocumentMode(True)
        self.setUsesScrollButtons(True)
        self.setMovable(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(True)

        bar = _MagicTabBar(self)
        bar.empty_double_clicked.connect(self.empty_area_double_clicked.emit)
        bar.tab_context_menu.connect(self._on_tab_context_menu)
        self.setTabBar(bar)
        bar.setMovable(True)
        self.setMovable(True)

        self._close_color = "#94A3B8"
        self._close_filter = _CloseButtonFilter(self)
        self._strip_filter = _StripClickFilter(self)
        self.installEventFilter(self._strip_filter)
        self._store = TabGroupStore()
        self._group_animator = TabGroupAnimator(self)
        self._drop_filter = TabGroupDropFilter(self, self._group_animator)
        bar.installEventFilter(self._drop_filter)
        self._middle_click_close = True
        self._show_scroll_buttons = True
        self._tr = None

        self._scroll_left = self._make_nav_button("◀", self._t("tabs.prev", "Previous tabs"))
        self._scroll_right = self._make_nav_button("▶", self._t("tabs.next", "Next tabs"))
        self._scroll_left.clicked.connect(lambda: self._scroll_tabs(-1))
        self._scroll_right.clicked.connect(lambda: self._scroll_tabs(1))

        self._new_tab_btn = QToolButton(self)
        self._new_tab_btn.setObjectName("tabNewButton")
        self._new_tab_btn.setAutoRaise(True)
        self._new_tab_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._new_tab_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._new_tab_btn.setFixedSize(22, 22)
        self._new_tab_btn.setIconSize(QSize(14, 14))
        self._new_tab_btn.setToolTip(self._t("tabs.new_file", "New file"))
        self._new_tab_btn.clicked.connect(self.empty_area_double_clicked.emit)

        left_wrap = QWidget(self)
        left_wrap.setObjectName("tabCornerLeft")
        ll = QHBoxLayout(left_wrap)
        ll.setContentsMargins(2, 0, 2, 0)
        ll.setSpacing(0)
        ll.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        ll.addWidget(self._scroll_left)

        right_wrap = QWidget(self)
        right_wrap.setObjectName("tabCornerRight")
        rl = QHBoxLayout(right_wrap)
        rl.setContentsMargins(2, 0, 4, 0)
        rl.setSpacing(2)
        rl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        rl.addWidget(self._scroll_right)
        rl.addWidget(self._new_tab_btn)

        self.setCornerWidget(left_wrap, Qt.Corner.TopLeftCorner)
        self.setCornerWidget(right_wrap, Qt.Corner.TopRightCorner)
        self._refresh_new_tab_icon()
        self.currentChanged.connect(lambda _i: self._update_scroll_buttons())
        self._update_scroll_buttons()

    def _t(self, key: str, default: str, **kwargs: object) -> str:
        tr = self._tr
        text = tr.t(key, default) if tr is not None and hasattr(tr, "t") else default
        return text.format(**kwargs) if kwargs else text

    def set_translator(self, tr: object | None) -> None:
        self._tr = tr
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        self._scroll_left.setToolTip(self._t("tabs.prev", "Previous tabs"))
        self._scroll_right.setToolTip(self._t("tabs.next", "Next tabs"))
        self._new_tab_btn.setToolTip(self._t("tabs.new_file", "New file"))
        bar = self.tabBar()
        for i in range(bar.count()):
            btn = bar.tabButton(i, QTabBar.ButtonPosition.RightSide)
            if isinstance(btn, QToolButton):
                btn.setToolTip(self._t("tabs.close", "Close"))

    def _make_nav_button(self, text: str, tip: str) -> QToolButton:
        btn = QToolButton(self)
        btn.setObjectName("tabScrollButton")
        btn.setAutoRaise(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.setFixedSize(22, 22)
        btn.setText(text)
        btn.setToolTip(tip)
        return btn

    def set_close_icon_color(self, color: str) -> None:
        self._close_color = color
        bar = self.tabBar()
        for i in range(bar.count()):
            btn = bar.tabButton(i, QTabBar.ButtonPosition.RightSide)
            if isinstance(btn, QToolButton):
                btn.setIcon(make_icon("tab_close", color))
        self._refresh_new_tab_icon()

    def apply_chrome_prefs(
        self,
        *,
        height: int = 30,
        min_width: int = 72,
        max_width: int = 220,
        show_scroll_buttons: bool = True,
        middle_click_close: bool = True,
    ) -> None:
        """Apply user tab chrome preferences from settings."""
        self._middle_click_close = bool(middle_click_close)
        self._show_scroll_buttons = bool(show_scroll_buttons)
        bar = self.tabBar()
        if isinstance(bar, _MagicTabBar):
            bar.set_chrome_metrics(height, min_width, max_width)
        self._update_scroll_buttons()

    def _refresh_new_tab_icon(self) -> None:
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
        bar = self.tabBar()
        if not bar.isMovable():
            bar.setMovable(True)
        self._refresh_group_paint()
        self._update_scroll_buttons()

    def tabRemoved(self, index: int) -> None:
        super().tabRemoved(index)
        live = {id(self.widget(i)) for i in range(self.count()) if self.widget(i)}
        self._store.prune(live)
        self._refresh_group_paint()
        self._update_scroll_buttons()

    def _install_close_button(self, index: int) -> None:
        bar = self.tabBar()
        btn = QToolButton(self)
        btn.setObjectName("tabCloseButton")
        btn.setAutoRaise(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.setFixedSize(16, 16)
        btn.setIconSize(QSize(10, 10))
        btn.setIcon(make_icon("tab_close", self._close_color))
        btn.setToolTip(self._t("tabs.close", "Close"))
        btn.setAttribute(Qt.WidgetAttribute.WA_LayoutUsesWidgetRect, True)
        btn.installEventFilter(self._close_filter)
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

    def _scroll_tabs(self, direction: int) -> None:
        bar = self.tabBar()
        if bar.count() == 0:
            return
        cur = self.currentIndex()
        step = 1 if direction > 0 else -1
        nxt = cur + step
        while 0 <= nxt < bar.count() and not bar.isTabVisible(nxt):
            nxt += step
        if 0 <= nxt < bar.count():
            self.setCurrentIndex(nxt)
        self._update_scroll_buttons()

    def _update_scroll_buttons(self) -> None:
        n = self.count()
        overflow = n > 1 and self._show_scroll_buttons
        self._scroll_left.setEnabled(n > 1 and self.currentIndex() > 0)
        self._scroll_right.setEnabled(n > 1 and self.currentIndex() < n - 1)
        self._scroll_left.setVisible(overflow)
        self._scroll_right.setVisible(overflow)

    def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().resizeEvent(event)
        self._update_scroll_buttons()

    # --- Groups -------------------------------------------------------

    def group_of_index(self, index: int) -> TabGroup | None:
        w = self.widget(index)
        return self._store.group_of_widget(id(w)) if w is not None else None

    def create_group(
        self,
        indices: list[int],
        *,
        name: str | None = None,
        color: str | None = None,
    ) -> TabGroup | None:
        wids = []
        for idx in indices:
            w = self.widget(idx)
            if w is not None:
                wids.append(id(w))
        group = self._store.create(wids, name=name, color=color)
        if group is not None:
            self._refresh_group_paint()
            self.groups_changed.emit()
        return group

    def add_to_group(self, index: int, group_id: str) -> None:
        w = self.widget(index)
        if w is None:
            return
        self._store.add(id(w), group_id)
        self._refresh_group_paint()
        group = self._store.groups.get(group_id)
        if group is not None:
            self._group_animator.pulse(self.tabBar(), index, group.color)
        self.groups_changed.emit()

    def remove_from_group(self, index: int) -> None:
        w = self.widget(index)
        if w is None:
            return
        self._group_animator.stop_index(self.tabBar(), index)
        self._store.remove(id(w))
        self._refresh_group_paint()
        self.groups_changed.emit()

    def set_group_collapsed(self, group_id: str, collapsed: bool) -> None:
        group = self._store.set_collapsed(group_id, collapsed)
        if group is None:
            return
        bar = self.tabBar()
        visible_kept = False
        for i in range(self.count()):
            w = self.widget(i)
            if w is None or id(w) not in group.members:
                continue
            if collapsed:
                if not visible_kept:
                    bar.setTabVisible(i, True)
                    title = self.tabText(i)
                    if not title.startswith("▸ ") and not title.startswith("▾ "):
                        self.setTabText(i, f"▸ {group.name}")
                    visible_kept = True
                else:
                    bar.setTabVisible(i, False)
            else:
                bar.setTabVisible(i, True)
                title = self.tabText(i)
                if (title.startswith("▸ ") or title.startswith("▾ ")) and isinstance(w, EditorTab):
                    star = " *" if w.document.modified else ""
                    self.setTabText(i, f"{w.document.title}{star}")
        self._refresh_group_paint()
        self.groups_changed.emit()

    def rename_group(self, group_id: str, name: str) -> None:
        self._store.rename(group_id, name)
        self.groups_changed.emit()

    def set_group_color(self, group_id: str, color: str) -> None:
        self._store.set_color(group_id, color)
        self._refresh_group_paint()
        self.groups_changed.emit()

    def list_groups(self) -> list[TabGroup]:
        return list(self._store.groups.values())

    def _refresh_group_paint(self) -> None:
        bar = self.tabBar()
        idx_map = {i: id(w) for i in range(self.count()) if (w := self.widget(i)) is not None}
        mapping = self._store.color_map_for_indices(idx_map)
        if isinstance(bar, _MagicTabBar):
            bar.set_group_colors(mapping)
        for i in mapping:
            g = self.group_of_index(i)
            if g:
                base = self.tabToolTip(i) or self.tabText(i)
                if f"[{g.name}]" not in base:
                    self.setTabToolTip(i, f"{base}  [{g.name}]")

    def _on_tab_context_menu(self, index: int, global_pos: QPoint) -> None:
        show_tab_context_menu(self, index, global_pos)

    def _hit_empty_strip(self, local: QPoint) -> bool:
        bar = self.tabBar()
        strip_top = bar.y()
        strip_bottom = bar.y() + max(bar.height(), 28)
        if not (strip_top <= local.y() <= strip_bottom):
            return False
        bar_pos = bar.mapFrom(self, local)
        if bar.tabAt(bar_pos) >= 0:
            return False
        for corner in (
            self.cornerWidget(Qt.Corner.TopRightCorner),
            self.cornerWidget(Qt.Corner.TopLeftCorner),
        ):
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
        if (
            event is not None
            and event.button() == Qt.MouseButton.MiddleButton
            and self._middle_click_close
        ):
            bar = self.tabBar()
            bar_pos = bar.mapFrom(self, event.position().toPoint())
            idx = bar.tabAt(bar_pos)
            if idx >= 0:
                self.tabCloseRequested.emit(idx)
                return
        super().mousePressEvent(event)
