"""VirtualEditor replace / undo (requires Qt)."""

from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")
pytest.importorskip("pytestqt")

from magiceditor.core.piece_table import PieceTable
from magiceditor.services.document import Document
from magiceditor.ui.virtual_editor import VirtualEditor
from magiceditor.ui.virtual_metrics import text_area_width, visible_line_slots


@pytest.mark.ui
def test_insert_uses_extracted_edit_path(qtbot) -> None:
    """J1.1: VirtualEditor.insert delegates to virtual_edit.insert_at_cursor."""
    doc = Document.from_text("ab")
    ed = VirtualEditor(doc)
    qtbot.addWidget(ed)
    ed.goto_line(0, 1)
    ed.insert("X")
    assert doc.text() == "aXb"


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


@pytest.mark.ui
def test_virtual_regex_find_replace(qtbot) -> None:
    doc = Document.from_text("x12 y34 z")
    doc.huge_mode = True
    ed = VirtualEditor(doc)
    qtbot.addWidget(ed)
    ed.goto_line(0, 0)
    assert ed.find_text(r"\d+", use_regex=True)
    line, col = ed.cursor_line_col()
    assert line == 1
    assert col == 2  # 1-based, at '1' of 12
    assert ed.replace_text(r"\d+", "N", use_regex=True)
    assert b"xN" in doc.buffer.get_text()


@pytest.mark.ui
def test_backspace_removes_full_multibyte_char(qtbot) -> None:
    """Regression: single-cursor backspace deleted 1 raw byte, splitting
    UTF-8 sequences and decoding to U+FFFD."""
    doc = Document.from_text("ção")
    ed = VirtualEditor(doc)
    qtbot.addWidget(ed)
    ed.goto_line(0, 3)
    ed._backspace()
    assert doc.text() == "çã"
    ed._backspace()
    assert doc.text() == "ç"
    assert "�" not in doc.text()


@pytest.mark.ui
def test_backspace_removes_full_emoji(qtbot) -> None:
    doc = Document.from_text("a\U0001f600b")
    ed = VirtualEditor(doc)
    qtbot.addWidget(ed)
    ed.goto_line(0, 2)
    ed._backspace()
    assert doc.text() == "ab"
    assert "�" not in doc.text()


@pytest.mark.ui
def test_backspace_at_line_start_joins_lines(qtbot) -> None:
    for text in ("ab\ncd", "ab\r\ncd"):
        doc = Document.from_text(text)
        ed = VirtualEditor(doc)
        qtbot.addWidget(ed)
        ed.goto_line(1, 0)
        ed._backspace()
        assert doc.text() == "abcd"
        assert "�" not in doc.text()


@pytest.mark.ui
def test_delete_forward_multibyte_and_emoji(qtbot) -> None:
    doc = Document.from_text("ção")
    ed = VirtualEditor(doc)
    qtbot.addWidget(ed)
    ed.goto_line(0, 0)
    ed._delete_forward()
    assert doc.text() == "ão"
    ed._delete_forward()
    assert doc.text() == "o"
    assert "�" not in doc.text()

    doc2 = Document.from_text("\U0001f600x")
    ed2 = VirtualEditor(doc2)
    qtbot.addWidget(ed2)
    ed2.goto_line(0, 0)
    ed2._delete_forward()
    assert doc2.text() == "x"
    assert "�" not in doc2.text()


@pytest.mark.ui
def test_delete_forward_at_eol_removes_whole_terminator(qtbot) -> None:
    for text in ("ab\ncd", "ab\r\ncd"):
        doc = Document.from_text(text)
        ed = VirtualEditor(doc)
        qtbot.addWidget(ed)
        ed.goto_line(0, 2)
        ed._delete_forward()
        assert doc.text() == "abcd"
        assert "�" not in doc.text()
        # Cursor stays put (end of the merged line content).
        assert ed.cursor_line_col() == (1, 3)


@pytest.mark.ui
def test_fast_backspace_multibyte_with_click_anchor(qtbot) -> None:
    """Holding backspace after a click used to leave a selection behind and,
    once a UTF-8 sequence was split, rewrite it as U+FFFD."""
    text = "Não é uma ação rápida"
    doc = Document.from_text(text)
    ed = VirtualEditor(doc)
    qtbot.addWidget(ed)
    ed.goto_line(0, len(text))
    ed._anchor_line = ed._cursor_line
    ed._anchor_col = ed._cursor_col
    for _ in range(len(text)):
        ed._backspace()
    assert doc.text() == ""
    assert "�" not in doc.buffer.get_text().decode("utf-8", "replace")


@pytest.mark.ui
def test_backspace_invalid_utf8_does_not_spread(qtbot) -> None:
    doc = Document(buffer=PieceTable(b"ab\xc3cd"), path=None, encoding="utf-8", eol="LF", title="t")
    ed = VirtualEditor(doc)
    qtbot.addWidget(ed)
    shown = doc.line_text(0)
    ed.goto_line(0, len(shown))
    before = len(doc.buffer)
    ed._backspace()
    assert len(doc.buffer) < before
    assert len(doc.buffer) >= before - 2
    for _ in range(8):
        ed._backspace()
    assert doc.buffer.get_text() == b""


@pytest.mark.ui
def test_backspace_removes_combining_grapheme(qtbot) -> None:
    doc = Document.from_text("cafe\u0301")
    ed = VirtualEditor(doc)
    qtbot.addWidget(ed)
    ed.goto_line(0, len("cafe\u0301"))
    ed._backspace()
    assert doc.text() == "caf"
    assert "�" not in doc.text()


@pytest.mark.ui
def test_backspace_utf16_single_line(qtbot) -> None:
    raw = "ção".encode("utf-16-le")
    doc = Document(
        buffer=PieceTable(raw),
        path=None,
        encoding="utf-16-le",
        eol="LF",
        title="t",
    )
    ed = VirtualEditor(doc)
    qtbot.addWidget(ed)
    ed.goto_line(0, 3)
    ed._backspace()
    assert doc.text() == "çã"
    ed.goto_line(0, 0)
    ed._delete_forward()
    assert doc.text() == "ã"
    assert "�" not in doc.text()


@pytest.mark.ui
def test_set_word_wrap_recomputes_scrollbar_range(qtbot) -> None:
    """Regression: set_word_wrap only set the flag — the scrollbar range
    stayed in unwrapped mode and wrapped tails rendered below the footer."""
    probe = VirtualEditor(Document.from_text("x"))
    qtbot.addWidget(probe)
    probe.resize(400, 200)
    char_w = max(1, probe.fontMetrics().horizontalAdvance(" "))
    per_row = max(1, text_area_width(probe) // char_w)
    long_line = "x" * (per_row + 1)  # wraps to exactly 2 display rows
    doc = Document.from_text("\n".join([long_line] * 40))
    ed = VirtualEditor(doc)
    qtbot.addWidget(ed)
    ed.resize(400, 200)
    sb = ed.verticalScrollBar()
    visible = visible_line_slots(ed)
    assert sb.maximum() == max(0, 40 - visible)
    ed.set_word_wrap(True)
    expected = min(40 - visible // 2, 39)
    assert sb.maximum() == expected
    assert sb.maximum() > max(0, 40 - visible)


@pytest.mark.ui
def test_wrapped_caret_scrolls_above_footer(qtbot) -> None:
    """Typing a wrap on the last visible line must scroll the new row up."""
    probe = VirtualEditor(Document.from_text("x"))
    qtbot.addWidget(probe)
    probe.resize(420, 220)
    probe.set_word_wrap(True)
    char_w = max(1, probe.fontMetrics().horizontalAdvance(" "))
    per_row = max(1, text_area_width(probe) // char_w)
    long_line = "x" * (per_row + 4)
    visible = visible_line_slots(probe)
    assert visible >= 3
    lines = ["a"] * (visible - 1) + [long_line]
    ed = VirtualEditor(Document.from_text("\n".join(lines)))
    qtbot.addWidget(ed)
    ed.resize(420, 220)
    ed.set_word_wrap(True)
    ed.goto_line(visible - 1, len(long_line))
    assert ed.verticalScrollBar().value() > 0
