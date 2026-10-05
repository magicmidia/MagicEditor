"""Tab context menu (group actions + close) extracted from TabManager."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QPoint
from PyQt6.QtWidgets import QInputDialog, QMenu

from magiceditor.ui.tab_groups import GROUP_COLORS

if TYPE_CHECKING:
    from magiceditor.ui.tab_manager import TabManager


def show_tab_context_menu(manager: TabManager, index: int, global_pos: QPoint) -> None:
    """Build and exec the tab context menu for ``manager``'s tab ``index``."""
    menu = QMenu(manager)
    if index < 0:
        act_new = menu.addAction(manager._t("tabs.new_tab", "New tab"))
        chosen = menu.exec(global_pos)
        if chosen is act_new:
            manager.empty_area_double_clicked.emit()
        return

    group = manager.group_of_index(index)
    act_new_group = menu.addAction(manager._t("tabs.new_group", "New group with this tab"))
    add_menu = menu.addMenu(manager._t("tabs.add_to_group", "Add to group"))
    if manager._store.groups:
        for g in manager._store.groups.values():
            act = add_menu.addAction(g.name)
            act.setData(g.group_id)
    else:
        add_menu.setEnabled(False)

    act_remove = act_rename = act_collapse = act_expand = None
    color_menu = None
    if group is not None:
        act_remove = menu.addAction(
            manager._t("tabs.remove_from_group", "Remove from “{name}”", name=group.name)
        )
        act_rename = menu.addAction(manager._t("tabs.rename_group", "Rename group…"))
        color_menu = menu.addMenu(manager._t("tabs.group_color", "Group color"))
        for label, hex_c in GROUP_COLORS:
            ca = color_menu.addAction(label.capitalize())
            ca.setData(hex_c)
        if group.collapsed:
            act_expand = menu.addAction(manager._t("tabs.expand_group", "Expand group"))
        else:
            act_collapse = menu.addAction(manager._t("tabs.collapse_group", "Collapse group"))

    menu.addSeparator()
    act_close = menu.addAction(manager._t("tabs.close_tab", "Close tab"))
    act_close_others = menu.addAction(manager._t("tabs.close_others", "Close others"))

    chosen = menu.exec(global_pos)
    if chosen is None:
        return
    if chosen is act_new_group:
        name, ok = QInputDialog.getText(
            manager,
            manager._t("tabs.group_title", "Tab group"),
            manager._t("tabs.group_name", "Group name:"),
        )
        manager.create_group([index], name=name if ok and name.strip() else None)
        return
    if chosen is act_remove:
        manager.remove_from_group(index)
        return
    if chosen is act_rename and group is not None:
        name, ok = QInputDialog.getText(
            manager,
            manager._t("tabs.rename_title", "Rename group"),
            manager._t("tabs.rename_name", "Name:"),
            text=group.name,
        )
        if ok and name.strip():
            manager.rename_group(group.group_id, name)
        return
    if chosen is act_collapse and group is not None:
        manager.set_group_collapsed(group.group_id, True)
        return
    if chosen is act_expand and group is not None:
        manager.set_group_collapsed(group.group_id, False)
        return
    if chosen is act_close:
        manager.tabCloseRequested.emit(index)
        return
    if chosen is act_close_others:
        for i in range(manager.count() - 1, -1, -1):
            if i != index:
                manager.tabCloseRequested.emit(i)
        return
    if chosen.parent() is add_menu:
        gid = chosen.data()
        if isinstance(gid, str):
            manager.add_to_group(index, gid)
        return
    if color_menu is not None and chosen.parent() is color_menu and group:
        hex_c = chosen.data()
        if isinstance(hex_c, str):
            manager.set_group_color(group.group_id, hex_c)
