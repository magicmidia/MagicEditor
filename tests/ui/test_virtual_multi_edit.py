"""Ship-path tests: multi-cursor / column insert on VirtualEditor.

Includes **keyPressEvent** path (product typing), not only _insert_at_cursor.
"""

from __future__ import annotations

import os

import pytest

pytest.importorskip("PyQt6")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication

from magiceditor.services.document import Document
from magiceditor.ui.virtual_editor import VirtualEditor


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _type_char(ed: VirtualEditor, ch: str) -> None:
    """Drive the real keyboard path used by the product."""
    key = ord(ch.upper()) if ch.isalpha() else ord(ch)
    event = QKeyEvent(
        QKeyEvent.Type.KeyPress,
        key,
        Qt.KeyboardModifier.NoModifier,
        ch,
    )
    ed.keyPressEvent(event)


def test_multi_cursor_insert_all_carets(qapp) -> None:
    doc = Document.from_text("aa\nbb\ncc\n")
    ed = VirtualEditor(doc)
    ed._cursor_line = 0
    ed._cursor_col = 1
    ed._extra_cursors = [(1, 1, 1), (2, 1, 1)]
    ed._insert_at_cursor("X")
    lines = doc.text().replace("\r\n", "\n").splitlines()
    assert all("X" in ln for ln in lines[:3])


def test_multi_cursor_keypath_types_all_carets(qapp) -> None:
    """MULTI_KEYPATH: typing must not wipe multi-cursor before insert."""
    doc = Document.from_text("aa\nbb\ncc\n")
    ed = VirtualEditor(doc)
    ed.show()
    ed.setFocus()
    ed._cursor_line = 0
    ed._cursor_col = 1
    ed._extra_cursors = [(1, 1, 1), (2, 1, 1)]
    _type_char(ed, "X")
    lines = [doc.line_text(i) for i in range(3)]
    assert all("X" in ln for ln in lines), f"keypath multi failed: {lines!r}"
    # Prefer aXa / bXb / cXc shape
    assert lines[0][1] == "X"
    assert lines[1][1] == "X"
    assert lines[2][1] == "X"


def test_multi_cursor_keypath_two_chars_all_carets(qapp) -> None:
    """MULTI_KEYPATH multi-char: second keystroke must still hit all N carets.

    Regression: restore used new_extras[:-1] after reverse-apply and dropped
    the bottom caret → 'XY' produced aXYa/bXYb/cXc (third line missing Y).
    """
    doc = Document.from_text("aa\nbb\ncc\n")
    ed = VirtualEditor(doc)
    ed.show()
    ed.setFocus()
    ed._cursor_line = 0
    ed._cursor_col = 1
    ed._extra_cursors = [(1, 1, 1), (2, 1, 1)]
    _type_char(ed, "X")
    _type_char(ed, "Y")
    lines = [doc.line_text(i) for i in range(3)]
    assert all("XY" in ln for ln in lines), f"expected XY on all lines, got {lines!r}"
    # N carets still active (1 primary + extras)
    n_carets = 1 + len(ed._extra_cursors)
    assert n_carets == 3, f"caret count {n_carets} after second char"


def test_column_rect_spans(qapp) -> None:
    doc = Document.from_text("abcd\nefgh\nijkl\n")
    ed = VirtualEditor(doc)
    ed._column_mode = True
    ed._anchor_line = 0
    ed._anchor_col = 1
    ed._cursor_line = 2
    ed._cursor_col = 3
    rect = ed._column_rect()
    assert rect == (0, 2, 1, 3)
    spans = ed._multi_edit_spans()
    assert len(spans) == 3
    assert spans[0][0] == 2


def test_column_insert(qapp) -> None:
    doc = Document.from_text("abcd\nefgh\nijkl\n")
    ed = VirtualEditor(doc)
    ed._column_mode = True
    ed._anchor_line = 0
    ed._anchor_col = 1
    ed._cursor_line = 2
    ed._cursor_col = 1  # zero-width column at col 1
    ed._insert_at_cursor("Z")
    lines = doc.text().replace("\r\n", "\n").splitlines()
    assert lines[0][1] == "Z"
    assert lines[1][1] == "Z"
    assert lines[2][1] == "Z"


def test_column_keypath_types_all_lines(qapp) -> None:
    """COL_KEYPATH: keyboard typing into column selection hits every line."""
    doc = Document.from_text("abcd\nefgh\nijkl\n")
    ed = VirtualEditor(doc)
    ed.show()
    ed.setFocus()
    ed._column_mode = True
    ed._column_anchor = (0, 1)
    ed._anchor_line = 0
    ed._anchor_col = 1
    ed._cursor_line = 2
    ed._cursor_col = 1
    assert ed._column_rect() is not None
    assert ed._multi_edit_spans()
    _type_char(ed, "Z")
    lines = [doc.line_text(i) for i in range(3)]
    assert lines[0][1] == "Z", f"line0={lines[0]!r}"
    assert lines[1][1] == "Z", f"line1={lines[1]!r}"
    assert lines[2][1] == "Z", f"line2={lines[2]!r}"


def test_column_keypath_two_chars_all_lines(qapp) -> None:
    """COL_KEYPATH multi-char: sequential column typing hits every line twice."""
    doc = Document.from_text("abcd\nefgh\nijkl\n")
    ed = VirtualEditor(doc)
    ed.show()
    ed.setFocus()
    ed._column_mode = True
    ed._column_anchor = (0, 1)
    ed._anchor_line = 0
    ed._anchor_col = 1
    ed._cursor_line = 2
    ed._cursor_col = 1
    _type_char(ed, "X")
    _type_char(ed, "Y")
    lines = [doc.line_text(i) for i in range(3)]
    assert all("XY" in ln for ln in lines), f"column multi-char failed: {lines!r}"


def test_snippet_expand_on_tab_path(qapp) -> None:
    doc = Document.from_text("def\n")
    ed = VirtualEditor(doc)
    ed.set_language("python")
    ed._cursor_line = 0
    ed._cursor_col = 3
    assert ed._try_snippet_or_complete() is True
    text = doc.text()
    assert "def " in text or ":" in text


def test_word_completion_applies(qapp) -> None:
    doc = Document.from_text("hello_world\nhel\n")
    ed = VirtualEditor(doc)
    ed.set_word_completion(True)
    ed._cursor_line = 1
    ed._cursor_col = 3  # after "hel"
    assert ed._try_snippet_or_complete() is True
    line = doc.line_text(1)
    assert line.startswith("hello_world") or "hello" in line
