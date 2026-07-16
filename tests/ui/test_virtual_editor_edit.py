"""VirtualEditor replace / undo (requires Qt)."""

from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")
pytest.importorskip("pytestqt")

from magiceditor.services.document import Document
from magiceditor.ui.virtual_editor import VirtualEditor


@pytest.mark.ui
def test_virtual_replace_all(qtbot) -> None:
    doc = Document.from_text("aa x aa x aa")
    doc.huge_mode = True
    ed = VirtualEditor(doc)
    qtbot.addWidget(ed)
    n = ed.replace_all_text("aa", "b")
    assert n == 3
    assert doc.buffer.get_text() == b"b x b x b"


@pytest.mark.ui
def test_virtual_undo_redo(qtbot) -> None:
    doc = Document.from_text("hi")
    doc.huge_mode = True
    ed = VirtualEditor(doc)
    qtbot.addWidget(ed)
    ed.goto_line(0, 2)
    # insert via public path
    ed._insert_at_cursor("!")
    assert doc.buffer.get_text() == b"hi!"
    ed.undo()
    assert doc.buffer.get_text() == b"hi"
    ed.redo()
    assert doc.buffer.get_text() == b"hi!"


@pytest.mark.ui
def test_virtual_replace_one(qtbot) -> None:
    doc = Document.from_text("one two one")
    doc.huge_mode = True
    ed = VirtualEditor(doc)
    qtbot.addWidget(ed)
    ed.goto_line(0, 0)
    assert ed.replace_text("one", "1")
    assert doc.buffer.get_text().startswith(b"1 ")
