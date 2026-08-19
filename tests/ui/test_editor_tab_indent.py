"""TAB stays in the editor; language follows the saved path."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PyQt6")
pytest.importorskip("pytestqt")

from PyQt6.QtCore import Qt

from magiceditor.services.document import Document
from magiceditor.ui.editor_tab import EditorTab
from magiceditor.ui.virtual_editor import VirtualEditor


@pytest.mark.ui
def test_preview_is_lazy_until_toggled(qtbot) -> None:
    tab = EditorTab(Document.from_text("# hi\n"))
    qtbot.addWidget(tab)
    assert tab.preview is None
    tab.toggle_preview()
    assert tab.preview is not None


@pytest.mark.ui
def test_tab_does_not_cycle_focus_and_inserts_indent(qtbot) -> None:
    doc = Document.from_text("hi")
    ed = VirtualEditor(doc)
    qtbot.addWidget(ed)
    ed.show()
    ed.setFocus()
    ed.goto_line(0, 2)
    assert ed.focusNextPrevChild(True) is False
    qtbot.keyClick(ed, Qt.Key.Key_Tab)
    assert doc.text() == "hi    "


@pytest.mark.ui
def test_enter_auto_indents_python_block(qtbot) -> None:
    doc = Document.from_text("def foo():")
    ed = VirtualEditor(doc)
    ed.set_language("python")
    qtbot.addWidget(ed)
    ed.goto_line(0, len("def foo():"))
    qtbot.keyClick(ed, Qt.Key.Key_Return)
    assert doc.text().splitlines() == ["def foo():", "    "]


@pytest.mark.ui
def test_enter_at_column_zero_does_not_indent_python_def(qtbot) -> None:
    doc = Document.from_text("def foo():")
    ed = VirtualEditor(doc)
    ed.set_language("python")
    qtbot.addWidget(ed)
    ed.goto_line(0, 0)
    qtbot.keyClick(ed, Qt.Key.Key_Return)
    assert doc.text() == "\ndef foo():"


@pytest.mark.ui
def test_refresh_language_from_saved_path(qtbot, tmp_path: Path) -> None:
    doc = Document.from_text("def hello():\n    return 1\n")
    tab = EditorTab(doc)
    qtbot.addWidget(tab)
    assert tab.language == "text"
    dest = tmp_path / "hello.py"
    dest.write_text(doc.text(), encoding="utf-8")
    doc.path = dest
    doc.title = dest.name
    assert tab.refresh_language_from_path() == "python"
    assert tab.language == "python"
    assert isinstance(tab.editor, VirtualEditor)
    assert tab.editor.language() == "python"
