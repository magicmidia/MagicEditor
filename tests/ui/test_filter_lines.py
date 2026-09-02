"""Smoke tests for Filter Lines (P1): action wiring, dialog, worker, result tab."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from pathlib import Path

import pytest

pytest.importorskip("PyQt6")
pytest.importorskip("pytestqt")

from PyQt6.QtCore import QCoreApplication, QSettings
from PyQt6.QtWidgets import QDialog

from magiceditor.core.line_filter import make_matcher
from magiceditor.i18n.translator import TranslatorManager
from magiceditor.services.settings import AppSettings
from magiceditor.themes.manager import ThemeManager
from magiceditor.ui.filter_lines_dialog import FilterLinesDialog
from magiceditor.ui.filter_lines_worker import FilterLinesWorker
from magiceditor.ui.main_window import MainWindow


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
    """Process events until ``cond`` holds (queued worker signals included)."""
    for _ in range(rounds):
        QCoreApplication.processEvents()
        if cond():
            return True
    return False


@pytest.mark.ui
def test_filter_action_registered_and_enabled(qtbot, tmp_path: Path) -> None:
    window = _make_window(qtbot, tmp_path)
    try:
        assert "action.filter_lines" in window._actions
        tab = window.current_tab()
        assert tab is not None
        window._sync_doc_tool_actions(tab)
        assert window._actions["action.filter_lines"].isEnabled()
    finally:
        _close_clean(window)


@pytest.mark.ui
def test_filter_lines_end_to_end(qtbot, tmp_path: Path) -> None:
    window = _make_window(qtbot, tmp_path)
    try:
        tab = window.current_tab()
        assert tab is not None
        tab.editor.insert("info a\nERROR b\ninfo c\nERROR d")
        base_tabs = window.tabs.count()

        doc = tab.document
        dlg = FilterLinesDialog(
            line_count=doc.line_index().line_count,
            line_text=doc.line_text,
            tr=window._tr,
            parent=window,
        )
        qtbot.addWidget(dlg)
        dlg.result_ready.connect(window._open_filter_result)
        dlg.pattern_combo.setCurrentText("ERROR")
        dlg.start_filter()
        assert dlg._worker is not None
        assert _pump_until(lambda: window.tabs.count() == base_tabs + 1)

        result_tab = window.current_tab()
        assert result_tab is not None and result_tab is not tab
        assert result_tab.editor.toPlainText() == "2: ERROR b\n4: ERROR d"
        expected_title = window._tr.t("filter.tab_title", "Filtro: {pattern}").format(
            pattern="ERROR"
        )
        assert result_tab.document.title == expected_title
        assert result_tab.document.path is None
    finally:
        _close_clean(window)


@pytest.mark.ui
def test_filter_lines_invert_and_no_match(qtbot, tmp_path: Path) -> None:
    window = _make_window(qtbot, tmp_path)
    try:
        tab = window.current_tab()
        assert tab is not None
        tab.editor.insert("keep\nDROP\nkeep2")

        doc = tab.document
        dlg = FilterLinesDialog(
            line_count=doc.line_index().line_count,
            line_text=doc.line_text,
            tr=window._tr,
            parent=window,
        )
        qtbot.addWidget(dlg)
        results: list[tuple] = []
        dlg.result_ready.connect(lambda *args: results.append(args))
        dlg.pattern_combo.setCurrentText("DROP")
        dlg.invert_box.setChecked(True)
        dlg.start_filter()
        assert dlg._worker is not None
        assert _pump_until(lambda: bool(results))
        assert results[0][1] == "1: keep\n3: keep2"

        # No match → dialog stays open with a status message, no new tab.
        dlg2 = FilterLinesDialog(
            line_count=doc.line_index().line_count,
            line_text=doc.line_text,
            tr=window._tr,
            parent=window,
        )
        qtbot.addWidget(dlg2)
        dlg2.pattern_combo.setCurrentText("zzz-no-match")
        dlg2.start_filter()
        assert dlg2._worker is not None
        assert _pump_until(lambda: bool(dlg2._status.text()))
        assert dlg2.result() == QDialog.DialogCode.Rejected  # not accepted
    finally:
        _close_clean(window)


@pytest.mark.ui
def test_filter_dialog_invalid_regex_shows_error(qtbot, tmp_path: Path) -> None:
    window = _make_window(qtbot, tmp_path)
    try:
        tab = window.current_tab()
        assert tab is not None
        tab.editor.insert("x")
        doc = tab.document
        dlg = FilterLinesDialog(
            line_count=doc.line_index().line_count,
            line_text=doc.line_text,
            tr=window._tr,
            parent=window,
        )
        qtbot.addWidget(dlg)
        dlg.pattern_combo.setCurrentText("(unclosed")
        dlg.regex_box.setChecked(True)
        dlg.start_filter()
        assert dlg._worker is None
        assert "regex" in dlg._status.text().lower()
    finally:
        _close_clean(window)


@pytest.mark.ui
def test_filter_worker_cancel(qtbot) -> None:
    matcher = make_matcher("x", case_sensitive=False, use_regex=False)
    worker = FilterLinesWorker(
        line_count=100,
        line_text=lambda i: "x",
        matcher=matcher,
    )
    results: list[object] = []
    worker.finished_matches.connect(results.append)
    worker.request_cancel()
    worker.start()
    assert worker.wait(10_000)
    assert _pump_until(lambda: bool(results))
    assert results == [None]


@pytest.mark.ui
def test_filter_worker_truncates_at_max(qtbot) -> None:
    matcher = make_matcher("hit", case_sensitive=False, use_regex=False)
    worker = FilterLinesWorker(
        line_count=10,
        line_text=lambda i: f"hit {i}",
        matcher=matcher,
        max_matches=3,
    )
    results: list[object] = []
    worker.finished_matches.connect(results.append)
    worker.start()
    assert worker.wait(10_000)
    assert _pump_until(lambda: bool(results))
    lines, truncated = results[0]
    assert lines == ["1: hit 0", "2: hit 1", "3: hit 2"]
    assert truncated is True


@pytest.mark.ui
def test_filter_dialog_rejects_when_idle(qtbot, tmp_path: Path) -> None:
    window = _make_window(qtbot, tmp_path)
    try:
        tab = window.current_tab()
        assert tab is not None
        doc = tab.document
        dlg = FilterLinesDialog(
            line_count=doc.line_index().line_count,
            line_text=doc.line_text,
            tr=window._tr,
            parent=window,
        )
        qtbot.addWidget(dlg)
        dlg._on_cancel()
        assert dlg.result() == QDialog.DialogCode.Rejected
    finally:
        _close_clean(window)
