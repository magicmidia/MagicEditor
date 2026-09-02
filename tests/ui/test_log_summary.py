"""Smoke tests for Log Summary (P6): action wiring, dialog, worker, navigation."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from pathlib import Path

import pytest

pytest.importorskip("PyQt6")
pytest.importorskip("pytestqt")

from PyQt6.QtCore import QCoreApplication, QSettings
from PyQt6.QtGui import QTextDocument

from magiceditor.i18n.translator import TranslatorManager
from magiceditor.services.settings import AppSettings
from magiceditor.themes.manager import ThemeManager
from magiceditor.ui.log_summary_dialog import LogSummaryDialog
from magiceditor.ui.log_summary_worker import LogSummaryWorker
from magiceditor.ui.main_window import MainWindow
from magiceditor.ui.syntax_highlighter import MagicHighlighter

LOG_LINES = "INFO boot\nWARN disk\nERROR fail\nplain\nERROR again"


def _make_window(qtbot, tmp_path: Path) -> MainWindow:
    ini = tmp_path / "test_settings.ini"
    qs = QSettings(str(ini), QSettings.Format.IniFormat)
    settings = AppSettings(settings=qs)
    tr = TranslatorManager()
    with suppress(OSError):
        tr.load("en_US")
    window = MainWindow(translator=tr, themes=ThemeManager(), settings=settings)
    qtbot.addWidget(window)
    return window


def _close_clean(window: MainWindow) -> None:
    for i in range(window.tabs.count()):
        w = window.tabs.widget(i)
        if w is not None:
            w.document.modified = False
    window.close()


def _pump_until(cond: Callable[[], bool], rounds: int = 500) -> bool:
    for _ in range(rounds):
        QCoreApplication.processEvents()
        if cond():
            return True
    return False


@pytest.mark.ui
def test_log_summary_action_registered_and_enabled(qtbot, tmp_path: Path) -> None:
    window = _make_window(qtbot, tmp_path)
    try:
        assert "action.log_summary" in window._actions
        tab = window.current_tab()
        assert tab is not None
        window._sync_doc_tool_actions(tab)
        assert window._actions["action.log_summary"].isEnabled()
    finally:
        _close_clean(window)


@pytest.mark.ui
def test_log_summary_dialog_counts_and_navigation(qtbot, tmp_path: Path) -> None:
    window = _make_window(qtbot, tmp_path)
    try:
        tab = window.current_tab()
        assert tab is not None
        tab.editor.insert(LOG_LINES)
        doc = tab.document
        dlg = LogSummaryDialog(
            line_count=doc.line_index().line_count,
            line_text=doc.line_text,
            tr=window._tr,
            parent=window,
        )
        qtbot.addWidget(dlg)
        assert _pump_until(lambda: dlg.counts["error"] == 2)
        assert dlg.counts == {"error": 2, "warn": 1, "info": 1, "debug": 0}
        assert dlg._count_labels["error"].text() == "2"
        assert dlg._next_buttons["error"].isEnabled()
        assert not dlg._next_buttons["debug"].isEnabled()

        # "Go to next" from the dialog drives cursor navigation in the tab.
        dlg.goto_level_requested.connect(lambda level: window._goto_log_level(tab, level))
        tab.goto_line(1, 1)
        dlg._next_buttons["error"].click()
        assert tab.current_line() == 3
        dlg._next_buttons["error"].click()
        assert tab.current_line() == 5
        # Wrap-around: past the last ERROR, back to the first one.
        dlg._next_buttons["error"].click()
        assert tab.current_line() == 3
    finally:
        _close_clean(window)


@pytest.mark.ui
def test_log_summary_worker_counts_and_cancel(qtbot) -> None:
    lines = [f"ERROR {i}" if i % 2 == 0 else "plain" for i in range(100)]
    worker = LogSummaryWorker(line_count=100, line_text=lambda i: lines[i])
    results: list[object] = []
    worker.finished_counts.connect(results.append)
    worker.start()
    assert worker.wait(10_000)
    assert _pump_until(lambda: bool(results))
    assert results[0] == {"error": 50, "warn": 0, "info": 0, "debug": 0}

    worker2 = LogSummaryWorker(line_count=100, line_text=lambda i: "ERROR")
    results2: list[object] = []
    worker2.finished_counts.connect(results2.append)
    worker2.request_cancel()
    worker2.start()
    assert worker2.wait(10_000)
    assert _pump_until(lambda: bool(results2))
    assert results2 == [None]


@pytest.mark.ui
def test_log_highlight_formats_reach_highlighter(qtbot) -> None:
    doc = QTextDocument()
    hl = MagicHighlighter(doc, "log")
    assert "log_error" in hl._formats
    assert "log_debug" in hl._formats
    fmt = hl._formats["log_error"]
    assert fmt.fontWeight() > 400  # bold
    hl.set_light_theme(True)
    err_color = hl._formats["log_error"].foreground().color()
    assert err_color != hl._formats["log_info"].foreground().color()
