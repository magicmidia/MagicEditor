"""Smoke tests for the document-tools integration (Edit/Tools/View/File).

Covers: case/Base64/URL transforms on the selection, extra line ops,
insert date/time, Save All, Always-on-top, per-tab read-only guards and
the checksum/stats dialogs.
"""

from __future__ import annotations

import re
from contextlib import suppress
from pathlib import Path

import pytest

pytest.importorskip("PyQt6")
pytest.importorskip("pytestqt")

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import QMessageBox

from magiceditor.core.text_stats import stats_for_text
from magiceditor.i18n.translator import TranslatorManager
from magiceditor.services.settings import AppSettings
from magiceditor.themes.manager import ThemeManager
from magiceditor.ui.main_window import MainWindow

NEW_ACTIONS = (
    "action.save_all",
    "action.case_upper",
    "action.case_lower",
    "action.case_title",
    "action.case_sentence",
    "action.case_invert",
    "action.base64_encode",
    "action.base64_decode",
    "action.url_encode",
    "action.url_decode",
    "action.sort_by_length",
    "action.reverse_lines",
    "action.remove_duplicate_lines",
    "action.remove_consecutive_duplicates",
    "action.insert_datetime_iso",
    "action.insert_date_short",
    "action.insert_datetime_local",
    "action.insert_timestamp",
    "action.toggle_read_only",
    "action.always_on_top",
    "action.file_checksum",
    "action.doc_stats",
)


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


@pytest.mark.ui
def test_new_actions_registered(qtbot, tmp_path: Path) -> None:
    window = _make_window(qtbot, tmp_path)
    for key in NEW_ACTIONS:
        assert key in window._actions, key
    _close_clean(window)


@pytest.mark.ui
def test_convert_actions_require_selection(qtbot, tmp_path: Path) -> None:
    window = _make_window(qtbot, tmp_path)
    tab = window.current_tab()
    assert tab is not None
    tab.editor.insert("hello")
    window._sync_doc_tool_actions(tab)
    assert not window._actions["action.case_upper"].isEnabled()
    assert not window._actions["action.base64_encode"].isEnabled()

    tab.editor.select_all()
    window._sync_doc_tool_actions(tab)
    assert window._actions["action.case_upper"].isEnabled()
    assert window._actions["action.url_decode"].isEnabled()

    window._actions["action.case_upper"].trigger()
    assert tab.editor.toPlainText() == "HELLO"
    _close_clean(window)


@pytest.mark.ui
def test_base64_decode_invalid_warns_and_keeps_text(qtbot, tmp_path: Path, monkeypatch) -> None:
    window = _make_window(qtbot, tmp_path)
    tab = window.current_tab()
    assert tab is not None
    tab.editor.insert("not base64!!!")
    tab.editor.select_all()

    warned: list[str] = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: warned.append(str(args[2])) or QMessageBox.StandardButton.Ok,
    )
    window._actions["action.base64_decode"].trigger()
    assert warned, "invalid base64 must warn"
    assert tab.editor.toPlainText() == "not base64!!!"
    _close_clean(window)


@pytest.mark.ui
def test_base64_and_url_roundtrip(qtbot, tmp_path: Path) -> None:
    window = _make_window(qtbot, tmp_path)
    tab = window.current_tab()
    assert tab is not None
    tab.editor.insert("olá mundo")
    tab.editor.select_all()
    window._actions["action.base64_encode"].trigger()
    assert tab.editor.toPlainText() == "b2zDoSBtdW5kbw=="
    tab.editor.select_all()
    window._actions["action.base64_decode"].trigger()
    assert tab.editor.toPlainText() == "olá mundo"

    tab.editor.select_all()
    window._actions["action.url_encode"].trigger()
    assert "%" in tab.editor.toPlainText()
    tab.editor.select_all()
    window._actions["action.url_decode"].trigger()
    assert tab.editor.toPlainText() == "olá mundo"
    _close_clean(window)


@pytest.mark.ui
def test_extra_line_ops(qtbot, tmp_path: Path) -> None:
    window = _make_window(qtbot, tmp_path)
    tab = window.current_tab()
    assert tab is not None
    tab.editor.insert("bb\na\nbb\na\nc")
    window._actions["action.remove_duplicate_lines"].trigger()
    assert tab.editor.toPlainText() == "bb\na\nc"

    tab2 = window.new_document()
    tab2.editor.insert("cc\na\nbb")
    window._actions["action.sort_by_length"].trigger()
    assert tab2.editor.toPlainText() == "a\ncc\nbb"
    window._actions["action.reverse_lines"].trigger()
    assert tab2.editor.toPlainText() == "bb\ncc\na"
    _close_clean(window)


@pytest.mark.ui
def test_insert_datetime_formats(qtbot, tmp_path: Path) -> None:
    window = _make_window(qtbot, tmp_path)
    tab = window.current_tab()
    assert tab is not None
    window._actions["action.insert_datetime_iso"].trigger()
    assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", tab.editor.toPlainText())
    window._actions["action.insert_timestamp"].trigger()
    assert re.search(r"\d{9,}", tab.editor.toPlainText())
    _close_clean(window)


@pytest.mark.ui
def test_read_only_blocks_edits_and_marks_tab(qtbot, tmp_path: Path) -> None:
    window = _make_window(qtbot, tmp_path)
    tab = window.current_tab()
    assert tab is not None
    tab.editor.insert("fixed")
    window._actions["action.toggle_read_only"].trigger()
    assert tab.editor.is_read_only()
    idx = window.tabs.currentIndex()
    assert "🔒" in window.tabs.tabText(idx)

    before = tab.editor.toPlainText()
    tab.editor.insert("x")
    tab.editor.paste()
    tab.editor.cut()
    assert tab.editor.toPlainText() == before

    window._sync_doc_tool_actions(tab)
    assert not window._actions["action.insert_timestamp"].isEnabled()
    window._actions["action.toggle_read_only"].trigger()
    assert not tab.editor.is_read_only()
    assert "🔒" not in window.tabs.tabText(idx)
    _close_clean(window)


@pytest.mark.ui
def test_save_all_saves_dirty_file_backed_tabs(qtbot, tmp_path: Path) -> None:
    window = _make_window(qtbot, tmp_path)
    p1 = tmp_path / "a.txt"
    p2 = tmp_path / "b.txt"
    p1.write_text("one", encoding="utf-8")
    p2.write_text("two", encoding="utf-8")
    t1 = window.open_path(p1)
    t2 = window.open_path(p2)
    assert t1 is not None and t2 is not None
    t1.editor.insert("X")
    t2.editor.insert("Y")
    untitled = window.new_document()
    untitled.editor.insert("draft")

    window.save_all()
    assert p1.read_text(encoding="utf-8").startswith("X")
    assert p2.read_text(encoding="utf-8").startswith("Y")
    assert not t1.document.modified
    assert not t2.document.modified
    # Untitled tabs stay dirty (no path to save to).
    assert untitled.document.modified
    _close_clean(window)


@pytest.mark.ui
def test_always_on_top_toggle(qtbot, tmp_path: Path) -> None:
    window = _make_window(qtbot, tmp_path)
    flag = Qt.WindowType.WindowStaysOnTopHint
    assert not window.windowFlags() & flag
    window._actions["action.always_on_top"].trigger()
    assert window.windowFlags() & flag
    assert window._actions["action.always_on_top"].isChecked()
    window._actions["action.always_on_top"].trigger()
    assert not window.windowFlags() & flag
    _close_clean(window)


@pytest.mark.ui
def test_checksum_action_requires_path(qtbot, tmp_path: Path) -> None:
    window = _make_window(qtbot, tmp_path)
    tab = window.current_tab()
    assert tab is not None
    window._sync_doc_tool_actions(tab)
    # Untitled tab: no path on disk → disabled.
    assert not window._actions["action.file_checksum"].isEnabled()
    _close_clean(window)


@pytest.mark.ui
def test_checksum_worker_hashes_file(qtbot, tmp_path: Path) -> None:
    from magiceditor.ui.checksum_dialog import ChecksumWorker

    p = tmp_path / "hash_me.txt"
    p.write_bytes(b"magic")
    worker = ChecksumWorker(p)
    results: list[dict] = []
    worker.finished_hashes.connect(results.append)
    worker.start()
    assert worker.wait(10_000)
    # Cross-thread signal is queued: pump the event loop to deliver it.
    from PyQt6.QtCore import QCoreApplication

    for _ in range(10):
        QCoreApplication.processEvents()
        if results:
            break
    assert len(results) == 1
    hashes = results[0]
    assert set(hashes) == {"md5", "sha1", "sha256"}
    assert hashes["md5"] == "2f3a4fccca6406e35bcf33e92dd93135"


@pytest.mark.ui
def test_stats_dialog_populates(qtbot) -> None:
    from PyQt6.QtWidgets import QLabel

    from magiceditor.ui.stats_dialog import StatsDialog

    stats = stats_for_text("one two\nthree\n")
    assert stats.words == 3 and stats.lines == 2
    dlg = StatsDialog(stats, encoding="utf-8", eol="LF", partial_bytes=2 * 1024 * 1024)
    qtbot.addWidget(dlg)
    texts = [lbl.text() for lbl in dlg.findChildren(QLabel)]
    assert f"{stats.chars:,}" in texts
    assert "UTF-8" in texts
    assert "LF" in texts
    note = dlg.findChild(QLabel, "statsPartialNote")
    assert note is not None and "2 MB" in note.text()
    dlg.close()
