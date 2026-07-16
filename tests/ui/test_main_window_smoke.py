"""Headless smoke test for MainWindow."""

from __future__ import annotations

from contextlib import suppress

import pytest

pytest.importorskip("PyQt6")
pytest.importorskip("pytestqt")

from magiceditor.i18n.translator import TranslatorManager
from magiceditor.themes.manager import ThemeManager
from magiceditor.ui.main_window import MainWindow


@pytest.mark.ui
def test_main_window_starts(qtbot, tmp_path) -> None:
    tr = TranslatorManager()
    with suppress(OSError):
        tr.load("en_US")
    themes = ThemeManager()
    window = MainWindow(translator=tr, themes=themes)
    qtbot.addWidget(window)
    assert window.tabs.count() >= 1
    tab = window.current_tab()
    assert tab is not None
    tab.editor.setPlainText("hello magic")
    assert "hello" in tab.editor.toPlainText()
