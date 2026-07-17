"""Clipboard: cut / copy / paste on VirtualEditor."""

from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")
pytest.importorskip("pytestqt")

from PyQt6.QtGui import QGuiApplication

from magiceditor.services.document import Document
from magiceditor.ui.virtual_editor import VirtualEditor


@pytest.mark.ui
def test_virtual_copy_paste(qtbot) -> None:
    doc = Document.from_text("hello world")
    doc.huge_mode = True
    ed = VirtualEditor(doc)
    qtbot.addWidget(ed)
    ed.goto_line(0, 0)
    ed._anchor_line = 0
    ed._anchor_col = 0
    ed._cursor_line = 0
    ed._cursor_col = 5
    assert ed.selected_text() == "hello"
    ed.copy()
    assert QGuiApplication.clipboard().text() == "hello"
    ed.goto_line(0, 11)
    ed.paste()
    assert b"hello" in doc.buffer.get_text()


@pytest.mark.ui
def test_virtual_cut_selection(qtbot) -> None:
    doc = Document.from_text("abc def")
    doc.huge_mode = True
    ed = VirtualEditor(doc)
    qtbot.addWidget(ed)
    ed._anchor_line = 0
    ed._anchor_col = 0
    ed._cursor_line = 0
    ed._cursor_col = 3
    ed.cut()
    assert QGuiApplication.clipboard().text() == "abc"
    assert doc.buffer.get_text() == b" def"


@pytest.mark.ui
def test_virtual_select_all(qtbot) -> None:
    doc = Document.from_text("one\ntwo")
    doc.huge_mode = True
    ed = VirtualEditor(doc)
    qtbot.addWidget(ed)
    ed.select_all()
    assert ed.has_selection()
    assert ed.selected_text() == "one\ntwo"
