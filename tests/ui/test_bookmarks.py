"""Bookmark navigation on VirtualEditor."""

from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")
pytest.importorskip("pytestqt")

from magiceditor.services.document import Document
from magiceditor.ui.virtual_editor import VirtualEditor


@pytest.mark.ui
def test_virtual_bookmarks(qtbot) -> None:
    doc = Document.from_text("a\nb\nc\nd\ne")
    doc.huge_mode = True
    ed = VirtualEditor(doc)
    qtbot.addWidget(ed)
    ed.goto_line(1, 0)
    ed.toggle_bookmark()
    ed.goto_line(3, 0)
    ed.toggle_bookmark()
    assert ed.has_bookmark(1)
    assert ed.has_bookmark(3)
    ed.goto_line(0, 0)
    assert ed.next_bookmark()
    assert ed.cursor_line_col()[0] == 2
    assert ed.next_bookmark()
    assert ed.cursor_line_col()[0] == 4
    assert ed.prev_bookmark()
    assert ed.cursor_line_col()[0] == 2
