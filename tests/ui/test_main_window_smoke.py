"""Headless smoke test for MainWindow."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path

import pytest

pytest.importorskip("PyQt6")
pytest.importorskip("pytestqt")

from PyQt6.QtCore import QSettings

from magiceditor.i18n.translator import TranslatorManager
from magiceditor.services.settings import AppSettings
from magiceditor.themes.manager import ThemeManager
from magiceditor.ui.main_window import MainWindow


@pytest.mark.ui
def test_main_window_starts(qtbot, tmp_path: Path) -> None:
    # Isolate from the developer's real session (which may reopen huge files).
    ini = tmp_path / "test_settings.ini"
    qs = QSettings(str(ini), QSettings.Format.IniFormat)
    settings = AppSettings(settings=qs)

    tr = TranslatorManager()
    with suppress(OSError):
        tr.load("en_US")
    themes = ThemeManager()
    window = MainWindow(translator=tr, themes=themes, settings=settings)
    qtbot.addWidget(window)
    assert window.tabs.count() >= 1
    tab = window.current_tab()
    assert tab is not None
    tab.editor.setPlainText("hello magic")
    assert "hello" in tab.editor.toPlainText()

    # Avoid modal "unsaved documents" dialog during teardown (blocks headless Qt).
    tab.document.modified = False
    if not tab.is_huge:
        tab.editor.document().setModified(False)  # type: ignore[union-attr]
    window.close()
