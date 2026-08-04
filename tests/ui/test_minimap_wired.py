"""Minimap is mounted on EditorTab and toggle affects visibility."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("PyQt6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from magiceditor.services.document import Document
from magiceditor.ui.editor_tab import EditorTab
from magiceditor.ui.minimap_widget import MinimapWidget


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_editor_tab_has_minimap_widget(qapp) -> None:
    tab = EditorTab(Document.from_text("a\nb\nc\n"))
    tab.show()
    assert isinstance(tab.minimap, MinimapWidget)
    assert tab.minimap.isHidden()
    tab.set_minimap_visible(True)
    assert not tab.minimap.isHidden()
    assert tab.minimap_visible() is True
    tab.set_minimap_visible(False)
    assert tab.minimap.isHidden()
