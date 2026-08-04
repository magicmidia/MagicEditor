"""VirtualEditor emits context_menu_requested on right-click."""

from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtCore import QPoint, QPointF, Qt  # noqa: E402
from PyQt6.QtGui import QMouseEvent  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from magiceditor.core.piece_table import PieceTable  # noqa: E402
from magiceditor.services.document import Document  # noqa: E402
from magiceditor.ui.virtual_editor import VirtualEditor  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _doc() -> Document:
    return Document(buffer=PieceTable("hello world\n"), title="Untitled")


def _right_press(local: QPoint, global_pos: QPoint) -> QMouseEvent:
    return QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(local),
        QPointF(global_pos),
        Qt.MouseButton.RightButton,
        Qt.MouseButton.RightButton,
        Qt.KeyboardModifier.NoModifier,
    )


def test_right_click_emits_context_menu(qapp) -> None:
    ed = VirtualEditor(_doc())
    ed.resize(400, 300)
    ed.show()
    qapp.processEvents()

    received: list[QPoint] = []
    ed.context_menu_requested.connect(received.append)

    local = QPoint(80, 40)
    ed.mousePressEvent(_right_press(local, ed.mapToGlobal(local)))
    qapp.processEvents()
    assert received, "context_menu_requested should fire on right-click"
    assert isinstance(received[0], QPoint)


def test_context_menu_can_be_disabled(qapp) -> None:
    ed = VirtualEditor(_doc())
    ed.set_context_menu_enabled(False)
    received: list[QPoint] = []
    ed.context_menu_requested.connect(received.append)
    ed.mousePressEvent(_right_press(QPoint(10, 10), QPoint(100, 100)))
    assert received == []
