from magiceditor.services.session_state import SessionState
from magiceditor.ui.spell_controller import (
    spell_word_at_caret,
    toggle_session_spell,
    word_on_line,
)


def test_word_on_line_at_caret() -> None:
    hit = word_on_line("hello world", 1)
    assert hit is not None
    assert hit[0] == "hello"
    assert word_on_line("   ", 0) is None


def test_toggle_session_spell_does_not_force() -> None:
    session = SessionState(spell_check=False, spell_force=None)
    toggle_session_spell(session)
    assert session.spell_check is True
    assert session.spell_force is None


def test_spell_word_at_caret_reads_only_caret_line() -> None:
    """K14: helper never walks the whole buffer — only line_text(cursor)."""

    class _Doc:
        def line_text(self, line: int) -> str:
            if line != 1:
                raise AssertionError("must not read other lines")
            return "alpha beta"

    class _Ed:
        _cursor_line = 1
        _cursor_col = 7
        _doc = _Doc()

    hit = spell_word_at_caret(_Ed())
    assert hit is not None
    assert hit[0] == "beta"


def test_spell_ignore_and_add_use_caret_helper() -> None:
    from pathlib import Path

    import magiceditor.ui.power_features as pf

    src = Path(pf.__file__).read_text(encoding="utf-8")
    ignore = src.split("def spell_ignore_word", 1)[1].split("def spell_add_word", 1)[0]
    add = src.split("def spell_add_word", 1)[1].split("def show_performance", 1)[0]
    assert "read_lines" not in ignore
    assert "read_lines" not in add
    assert "ignore_word_at_caret" in ignore
    assert "add_word_at_caret" in add


def test_ignore_and_add_at_caret_drive_engine() -> None:
    """K14 shipped path: caret helpers mutate SpellEngine without read_lines."""
    from magiceditor.core.spell import SpellEngine
    from magiceditor.ui.spell_controller import add_word_at_caret, ignore_word_at_caret

    class _Doc:
        def line_text(self, line: int) -> str:
            if line != 0:
                raise AssertionError("must not read other lines")
            return "xyzzy word"

    class _Ed:
        _cursor_line = 0
        _cursor_col = 1
        _doc = _Doc()

    eng = SpellEngine(language="en_US")
    assert ignore_word_at_caret(eng, _Ed()) == "xyzzy"
    assert "xyzzy" in eng.ignore_session
    assert add_word_at_caret(eng, _Ed()) == "xyzzy"
    assert "xyzzy" in eng.user_words


def test_mixin_spell_ignore_word_on_virtual_editor(qtbot) -> None:
    """K14: PowerFeaturesMixin.spell_ignore_word uses caret helper on VirtualEditor."""
    import pytest

    pytest.importorskip("PyQt6")
    pytest.importorskip("pytestqt")
    from magiceditor.core.document import Document
    from magiceditor.core.spell import SpellEngine
    from magiceditor.ui.power_features import PowerFeaturesMixin
    from magiceditor.ui.virtual_editor import VirtualEditor

    class _Tab:
        def __init__(self, editor) -> None:
            self.editor = editor

    class _Host:
        def __init__(self, tab) -> None:
            self._tab = tab
            self._spell_engine = SpellEngine(language="en_US")
            self._spell_engines: dict = {}

        def _current_tab(self):
            return self._tab

        spell_ignore_word = PowerFeaturesMixin.spell_ignore_word

    ed = VirtualEditor(Document.from_text("hello xyzzy"))
    qtbot.addWidget(ed)
    ed.goto_line(0, 7)
    host = _Host(_Tab(ed))
    host.spell_ignore_word()
    assert "xyzzy" in host._spell_engine.ignore_session
