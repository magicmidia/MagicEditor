"""Session restore of open files, bookmarks, and cursor."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path

import pytest

pytest.importorskip("PyQt6")
pytest.importorskip("pytestqt")

from PyQt6.QtCore import QSettings

from magiceditor.i18n.translator import TranslatorManager
from magiceditor.services.settings import AppSettings, SessionState, normalize_path
from magiceditor.themes.manager import ThemeManager
from magiceditor.ui.main_window import MainWindow


@pytest.mark.ui
def test_restore_open_tabs_bookmarks_cursor(qtbot, tmp_path: Path) -> None:
    f1 = tmp_path / "one.txt"
    f2 = tmp_path / "two.txt"
    f1.write_text("line1\nline2\nline3\n", encoding="utf-8")
    f2.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
    p1 = normalize_path(f1)
    p2 = normalize_path(f2)

    ini = tmp_path / "session.ini"
    qs = QSettings(str(ini), QSettings.Format.IniFormat)
    settings = AppSettings(settings=qs)
    settings.save(
        SessionState(
            open_files=[p1, p2],
            active_file=p2,
            bookmarks={p1: [1], p2: [0, 2]},
            cursors={p2: (3, 2)},
            workspace=str(tmp_path),
            word_wrap=False,
            line_numbers=True,
        )
    )

    tr = TranslatorManager()
    with suppress(OSError):
        tr.load("en_US")
    window = MainWindow(
        translator=tr,
        themes=ThemeManager(),
        settings=settings,
    )
    qtbot.addWidget(window)

    assert window.tabs.count() == 2
    paths = []
    for i in range(window.tabs.count()):
        tab = window.tabs.widget(i)
        assert tab is not None
        assert tab.document.path is not None
        paths.append(normalize_path(tab.document.path))
    assert paths == [p1, p2]

    # Active tab is second file
    cur = window.current_tab()
    assert cur is not None
    assert normalize_path(cur.document.path) == p2
    assert cur.get_bookmarks() == [0, 2]
    assert cur.current_line() == 3

    # First tab bookmarks
    t0 = window.tabs.widget(0)
    assert t0 is not None
    assert t0.get_bookmarks() == [1]

    # Collect session preserves list
    collected = window._collect_session()
    assert collected.open_files == [p1, p2]
    assert collected.active_file == p2
    assert collected.bookmarks[p2] == [0, 2]

    # Clean for teardown
    for i in range(window.tabs.count()):
        w = window.tabs.widget(i)
        if w is not None:
            w.document.modified = False
    window.close()
