"""Drag-to-group target resolution, drop filter and animations (offscreen)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QLabel

from magiceditor.ui.tab_group_anim import (
    TabGroupAnimator,
    fade_drop_highlight,
    pulse_stripe,
)
from magiceditor.ui.tab_group_drag import TabGroupDropFilter, drop_target_group
from magiceditor.ui.tab_manager import TabManager


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _manager_with_tabs(names: tuple[str, ...] = ("a", "b", "c")) -> TabManager:
    tabs = TabManager()
    for name in names:
        tabs.addTab(QLabel(name), f"{name}.txt")
    tabs.resize(640, 320)
    tabs.show()  # offscreen: needed so tabAt/tabRect have real geometry
    return tabs


def test_drop_target_in_group(qapp) -> None:
    tabs = _manager_with_tabs()
    g = tabs.create_group([0, 1], name="Work")
    assert g is not None
    bar = tabs.tabBar()
    pos = bar.tabRect(0).center()
    assert drop_target_group(bar, pos, 2) == g.group_id


def test_drop_target_without_group(qapp) -> None:
    tabs = _manager_with_tabs()
    tabs.create_group([0, 1], name="Work")
    bar = tabs.tabBar()
    pos = bar.tabRect(2).center()
    assert drop_target_group(bar, pos, 0) is None


def test_drop_target_over_own_tab(qapp) -> None:
    tabs = _manager_with_tabs()
    g = tabs.create_group([0, 1], name="Work")
    assert g is not None
    bar = tabs.tabBar()
    pos = bar.tabRect(1).center()
    assert drop_target_group(bar, pos, 1) is None


def test_drop_target_empty_area(qapp) -> None:
    tabs = _manager_with_tabs()
    tabs.create_group([0, 1], name="Work")
    bar = tabs.tabBar()
    assert drop_target_group(bar, QPoint(-50, -50), 2) is None


def test_drop_target_already_member(qapp) -> None:
    tabs = _manager_with_tabs()
    tabs.create_group([0, 1], name="Work")
    bar = tabs.tabBar()
    pos = bar.tabRect(1).center()
    assert drop_target_group(bar, pos, 0) is None


def test_drop_highlight_setters(qapp) -> None:
    tabs = _manager_with_tabs()
    bar = tabs.tabBar()
    bar.set_drop_highlight(1, "#3B82F6")
    assert bar._drop_highlight_index == 1
    assert bar._drop_highlight_color == "#3B82F6"
    assert bar._drop_highlight_alpha == 160
    bar.update()
    bar.clear_drop_highlight()
    assert bar._drop_highlight_index == -1
    assert bar._drop_highlight_alpha == 0


def test_fade_drop_highlight_runs_to_end(qapp) -> None:
    tabs = _manager_with_tabs()
    bar = tabs.tabBar()
    bar.set_drop_highlight(0, "#3B82F6")
    anim = fade_drop_highlight(bar)
    anim.setDuration(1)
    QTest.qWait(60)
    assert bar._drop_highlight_index == -1
    assert bar._drop_highlight_alpha == 0


def test_pulse_stripe_restores_at_end(qapp) -> None:
    tabs = _manager_with_tabs()
    tabs.create_group([0], name="Solo")
    bar = tabs.tabBar()
    anim = pulse_stripe(bar, 0, "#3B82F6")
    anim.setDuration(1)
    QTest.qWait(60)
    assert 0 not in bar._stripe_pulses


def test_animator_pulse_invalid_index(qapp) -> None:
    tabs = _manager_with_tabs()
    animator = TabGroupAnimator(tabs)
    assert animator.pulse(tabs.tabBar(), 99, "#3B82F6") is None
    assert animator.pulse(tabs.tabBar(), -1, "#3B82F6") is None


def test_animator_stop_all_clears(qapp) -> None:
    tabs = _manager_with_tabs()
    animator = TabGroupAnimator(tabs)
    assert animator.pulse(tabs.tabBar(), 0, "#3B82F6") is not None
    assert animator._active
    animator.stop_all()
    assert animator._active == {}


def test_animator_entry_removed_after_finish(qapp) -> None:
    tabs = _manager_with_tabs()
    animator = TabGroupAnimator(tabs)
    anim = animator.pulse(tabs.tabBar(), 0, "#3B82F6")
    assert anim is not None
    anim.setDuration(1)
    QTest.qWait(60)
    assert animator._active == {}


def test_drop_filter_adds_dragged_tab_to_group(qapp) -> None:
    tabs = _manager_with_tabs()
    g = tabs.create_group([0, 1], name="Work")
    assert g is not None
    bar = tabs.tabBar()
    dragged = tabs.widget(2)

    press_pos = bar.tabRect(2).center()
    target_pos = bar.tabRect(0).center()
    QTest.mousePress(bar, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, press_pos)
    # Move beyond startDragDistance towards the grouped tab.
    steps = 6
    for i in range(1, steps + 1):
        x = press_pos.x() + (target_pos.x() - press_pos.x()) * i // steps
        y = press_pos.y() + (target_pos.y() - press_pos.y()) * i // steps
        move = QMouseEvent(
            QEvent.Type.MouseMove,
            QPointF(x, y),
            QPointF(bar.mapToGlobal(QPoint(x, y))),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        QApplication.sendEvent(bar, move)
    QTest.mouseRelease(bar, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, target_pos)
    final = tabs.indexOf(dragged)
    assert final >= 0
    assert tabs.group_of_index(final) is g


def test_drop_filter_is_passive(qapp) -> None:
    tabs = _manager_with_tabs()
    bar = tabs.tabBar()
    filt = TabGroupDropFilter(tabs)
    press = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(bar.tabRect(0).center()),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    assert filt.eventFilter(bar, press) is False
