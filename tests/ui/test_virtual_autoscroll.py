"""Drag-select auto-scroll: viewport edge scrolling for VirtualEditor."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("PyQt6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtWidgets import QApplication

from magiceditor.core.document import Document
from magiceditor.core.piece_table import PieceTable
from magiceditor.ui import virtual_mouse
from magiceditor.ui.virtual_editor import VirtualEditor


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class _MoveEvent:
    def __init__(self, y: int) -> None:
        self._pos = QPoint(100, y)

    def position(self) -> QPointF:
        return QPointF(self._pos)

    def buttons(self) -> Qt.MouseButton:
        return Qt.MouseButton.LeftButton

    def accept(self) -> None:
        pass


class _ReleaseEvent:
    def button(self) -> Qt.MouseButton:
        return Qt.MouseButton.LeftButton

    def accept(self) -> None:
        pass


def _editor(qapp) -> VirtualEditor:
    doc = Document(
        buffer=PieceTable(("x\n" * 5000).encode()),
        path=None,
        encoding="utf-8",
        eol="LF",
        title="t",
    )
    ed = VirtualEditor(doc)
    ed.resize(400, 200)
    ed._selecting = True
    ed._anchor_line, ed._anchor_col = 0, 0
    return ed


def test_drag_below_edge_auto_scrolls_down(qapp) -> None:
    ed = _editor(qapp)
    virtual_mouse.handle_mouse_move(ed, _MoveEvent(ed.viewport().height() + 50))
    assert ed._auto_scroll_timer is not None
    assert ed._auto_scroll_timer.isActive()
    first = ed.verticalScrollBar().value()
    for _ in range(10):
        virtual_mouse._auto_scroll_tick(ed)
    assert ed.verticalScrollBar().value() > first
    assert ed._cursor_line > 0


def test_drag_above_top_scrolls_up_without_jumping_to_eof(qapp) -> None:
    ed = _editor(qapp)
    ed.verticalScrollBar().setValue(100)
    virtual_mouse.handle_mouse_move(ed, _MoveEvent(-80))
    assert ed._auto_scroll_dy == -80
    line_before = ed._cursor_line
    for _ in range(5):
        virtual_mouse._auto_scroll_tick(ed)
    # Regression: unclamped hit_test used to send the caret to the last line.
    assert ed._cursor_line < line_before
    assert ed._cursor_line < 1000
    assert ed.verticalScrollBar().value() < 100


def test_timer_stops_inside_viewport_and_on_release(qapp) -> None:
    ed = _editor(qapp)
    virtual_mouse.handle_mouse_move(ed, _MoveEvent(ed.viewport().height() + 20))
    assert ed._auto_scroll_timer is not None
    assert ed._auto_scroll_timer.isActive()
    virtual_mouse.handle_mouse_move(ed, _MoveEvent(50))
    assert ed._auto_scroll_dy == 0
    assert not ed._auto_scroll_timer.isActive()
    virtual_mouse.handle_mouse_move(ed, _MoveEvent(ed.viewport().height() + 20))
    virtual_mouse.handle_mouse_release(ed, _ReleaseEvent())
    assert not ed._auto_scroll_timer.isActive()
