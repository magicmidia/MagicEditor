"""Tab bar: movable reorder flag and empty double-click signal."""

from __future__ import annotations

import pytest
from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QLabel

from magiceditor.ui.magic_tab_bar import MagicTabBar
from magiceditor.ui.tab_filters import CloseButtonFilter, StripClickFilter
from magiceditor.ui.tab_manager import TabManager

pytestmark = pytest.mark.usefixtures("qapp")


def test_tab_manager_tooltips_follow_locale(qapp) -> None:
    """J2.4: tab chrome strings come from locales, not hardcoded PT."""
    from magiceditor.i18n.translator import TranslatorManager

    tr = TranslatorManager()
    tr.load("en_US")
    tabs = TabManager()
    tabs.set_translator(tr)
    assert tabs._new_tab_btn.toolTip() == "New file"
    assert "Novo arquivo" not in tabs._new_tab_btn.toolTip()
    tr.load("pt_BR")
    tabs.retranslate_ui()
    assert tabs._new_tab_btn.toolTip() == "Novo arquivo"


def test_tab_manager_uses_extracted_bar_and_filters(qapp) -> None:
    """J1.5: TabManager composes MagicTabBar + extracted filters."""
    tabs = TabManager()
    assert isinstance(tabs.tabBar(), MagicTabBar)
    assert isinstance(tabs._close_filter, CloseButtonFilter)
    assert isinstance(tabs._strip_filter, StripClickFilter)


def test_tab_bar_is_movable(qapp) -> None:
    tabs = TabManager()
    assert tabs.isMovable() is True
    assert tabs.tabBar().isMovable() is True
    tabs.addTab(QLabel("a"), "A")
    tabs.addTab(QLabel("b"), "B")
    # Movable must survive tab insertion
    assert tabs.tabBar().isMovable() is True


def test_empty_strip_hit_detects_free_area(qapp) -> None:
    tabs = TabManager()
    tabs.resize(600, 200)
    tabs.addTab(QLabel("only"), "Only")
    bar = tabs.tabBar()
    last = bar.tabRect(0)
    # Point to the right of the last tab, in the strip row
    local = QPoint(last.right() + 60, bar.y() + max(1, bar.height() // 2))
    if local.x() >= tabs.width():
        local = QPoint(tabs.width() - 40, local.y())
    # May be outside bar widget but still empty strip
    assert tabs._hit_empty_strip(local) is True or bar._is_empty_hit(bar.mapFrom(tabs, local))


def test_empty_double_click_on_bar_emits(qapp) -> None:
    tabs = TabManager()
    tabs.resize(600, 200)
    tabs.addTab(QLabel("only"), "Only")
    hits: list[int] = []
    tabs.empty_area_double_clicked.connect(lambda: hits.append(1))

    bar = tabs.tabBar()
    last = bar.tabRect(0)
    pos = QPoint(last.right() + 30, last.center().y())
    if bar.tabAt(pos) >= 0:
        pos = QPoint(bar.width() - 2, last.center().y())

    if bar.tabAt(pos) < 0:
        ev = QMouseEvent(
            QMouseEvent.Type.MouseButtonDblClick,
            QPointF(pos),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        bar.mouseDoubleClickEvent(ev)
        assert hits == [1]
    else:
        # Fallback: strip helper must still report empty somewhere
        assert tabs._hit_empty_strip(QPoint(tabs.width() - 30, bar.y() + 4))


def test_new_tab_corner_button_exists(qapp) -> None:
    tabs = TabManager()
    corner = tabs.cornerWidget(Qt.Corner.TopRightCorner)
    assert corner is not None
    # Corner may be a wrapper QWidget holding scroll + new buttons
    btn = getattr(tabs, "_new_tab_btn", None)
    assert btn is not None
    hits: list[int] = []
    tabs.empty_area_double_clicked.connect(lambda: hits.append(1))
    btn.click()
    assert hits == [1]
