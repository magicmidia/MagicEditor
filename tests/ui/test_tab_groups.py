"""Tab groups + scroll chrome (offscreen)."""

from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication, QLabel  # noqa: E402

from magiceditor.ui.tab_groups import GROUP_COLORS  # noqa: E402
from magiceditor.ui.tab_manager import TabManager  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_create_group_and_color(qapp) -> None:
    tabs = TabManager()
    a = QLabel("a")
    b = QLabel("b")
    c = QLabel("c")
    tabs.addTab(a, "a.txt")
    tabs.addTab(b, "b.txt")
    tabs.addTab(c, "c.txt")
    g = tabs.create_group([0, 1], name="Work", color=GROUP_COLORS[0][1])
    assert g is not None
    assert g.name == "Work"
    assert tabs.group_of_index(0) is g
    assert tabs.group_of_index(1) is g
    assert tabs.group_of_index(2) is None
    tabs.remove_from_group(1)
    assert tabs.group_of_index(1) is None
    assert tabs.group_of_index(0) is g


def test_collapse_group_hides_members(qapp) -> None:
    tabs = TabManager()
    for name in ("x", "y", "z"):
        tabs.addTab(QLabel(name), name)
    g = tabs.create_group([0, 1, 2], name="Pack")
    assert g is not None
    tabs.set_group_collapsed(g.group_id, True)
    bar = tabs.tabBar()
    visible = [i for i in range(tabs.count()) if bar.isTabVisible(i)]
    assert len(visible) == 1
    tabs.set_group_collapsed(g.group_id, False)
    visible = [i for i in range(tabs.count()) if bar.isTabVisible(i)]
    assert len(visible) == 3


def test_scroll_buttons_exist(qapp) -> None:
    tabs = TabManager()
    assert tabs._scroll_left is not None
    assert tabs._scroll_right is not None
    tabs.addTab(QLabel("1"), "1")
    tabs.addTab(QLabel("2"), "2")
    tabs._update_scroll_buttons()
    # Not shown without a parent window; still enabled for multi-tab nav.
    assert tabs._scroll_right.isEnabled()
