"""Tab widget: scroll, close danger hover, Chrome-style groups, empty double-click."""

from __future__ import annotations

from PyQt6.QtCore import QEvent, QObject, QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QMenu,
    QStyle,
    QTabBar,
    QTabWidget,
    QToolButton,
    QWidget,
)

from magiceditor.ui.editor_tab import EditorTab
from magiceditor.ui.icons import icon as make_icon
from magiceditor.ui.tab_groups import GROUP_COLORS, TabGroup, TabGroupStore


class _CloseButtonFilter(QObject):
    """Swap close icon to white on hover (danger QSS paints red background)."""

    def __init__(self, owner: TabManager) -> None:
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


class _MagicTabBar(QTabBar):
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
        self._pref_height = 28
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
                if isinstance(parent, TabManager) and parent._middle_click_close:
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


class _StripClickFilter(QObject):
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
        self._middle_click_close = True
        self._show_scroll_buttons = True

        self._scroll_left = self._make_nav_button("◀", "Abas anteriores")
        self._scroll_right = self._make_nav_button("▶", "Próximas abas")
        self._scroll_left.clicked.connect(lambda: self._scroll_tabs(-1))
        self._scroll_right.clicked.connect(lambda: self._scroll_tabs(1))

        self._new_tab_btn = QToolButton(self)
        self._new_tab_btn.setObjectName("tabNewButton")
        self._new_tab_btn.setAutoRaise(True)
        self._new_tab_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._new_tab_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._new_tab_btn.setFixedSize(22, 22)
        self._new_tab_btn.setIconSize(QSize(14, 14))
        self._new_tab_btn.setToolTip("Novo arquivo")
        self._new_tab_btn.clicked.connect(self.empty_area_double_clicked.emit)

        left_wrap = QWidget(self)
        left_wrap.setObjectName("tabCornerLeft")
        ll = QHBoxLayout(left_wrap)
        ll.setContentsMargins(2, 0, 2, 0)
        ll.setSpacing(0)
        ll.addWidget(self._scroll_left)

        right_wrap = QWidget(self)
        right_wrap.setObjectName("tabCornerRight")
        rl = QHBoxLayout(right_wrap)
        rl.setContentsMargins(2, 0, 4, 0)
        rl.setSpacing(2)
        rl.addWidget(self._scroll_right)
        rl.addWidget(self._new_tab_btn)

        self.setCornerWidget(left_wrap, Qt.Corner.TopLeftCorner)
        self.setCornerWidget(right_wrap, Qt.Corner.TopRightCorner)
        self._refresh_new_tab_icon()
        self.currentChanged.connect(lambda _i: self._update_scroll_buttons())
        self._update_scroll_buttons()

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
        height: int = 28,
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
        btn.setToolTip("Fechar")
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
        self.groups_changed.emit()

    def remove_from_group(self, index: int) -> None:
        w = self.widget(index)
        if w is None:
            return
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
        menu = QMenu(self)
        if index < 0:
            act_new = menu.addAction("Nova aba")
            chosen = menu.exec(global_pos)
            if chosen is act_new:
                self.empty_area_double_clicked.emit()
            return

        group = self.group_of_index(index)
        act_new_group = menu.addAction("Novo grupo com esta aba")
        add_menu = menu.addMenu("Adicionar ao grupo")
        if self._store.groups:
            for g in self._store.groups.values():
                act = add_menu.addAction(g.name)
                act.setData(g.group_id)
        else:
            add_menu.setEnabled(False)

        act_remove = act_rename = act_collapse = act_expand = None
        color_menu = None
        if group is not None:
            act_remove = menu.addAction(f"Remover de «{group.name}»")
            act_rename = menu.addAction("Renomear grupo…")
            color_menu = menu.addMenu("Cor do grupo")
            for label, hex_c in GROUP_COLORS:
                ca = color_menu.addAction(label.capitalize())
                ca.setData(hex_c)
            if group.collapsed:
                act_expand = menu.addAction("Expandir grupo")
            else:
                act_collapse = menu.addAction("Recolher grupo")

        menu.addSeparator()
        act_close = menu.addAction("Fechar aba")
        act_close_others = menu.addAction("Fechar outras")

        chosen = menu.exec(global_pos)
        if chosen is None:
            return
        if chosen is act_new_group:
            name, ok = QInputDialog.getText(self, "Grupo de abas", "Nome do grupo:")
            self.create_group([index], name=name if ok and name.strip() else None)
            return
        if chosen is act_remove:
            self.remove_from_group(index)
            return
        if chosen is act_rename and group is not None:
            name, ok = QInputDialog.getText(self, "Renomear grupo", "Nome:", text=group.name)
            if ok and name.strip():
                self.rename_group(group.group_id, name)
            return
        if chosen is act_collapse and group is not None:
            self.set_group_collapsed(group.group_id, True)
            return
        if chosen is act_expand and group is not None:
            self.set_group_collapsed(group.group_id, False)
            return
        if chosen is act_close:
            self.tabCloseRequested.emit(index)
            return
        if chosen is act_close_others:
            for i in range(self.count() - 1, -1, -1):
                if i != index:
                    self.tabCloseRequested.emit(i)
            return
        if chosen.parent() is add_menu:
            gid = chosen.data()
            if isinstance(gid, str):
                self.add_to_group(index, gid)
            return
        if color_menu is not None and chosen.parent() is color_menu and group:
            hex_c = chosen.data()
            if isinstance(hex_c, str):
                self.set_group_color(group.group_id, hex_c)

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
