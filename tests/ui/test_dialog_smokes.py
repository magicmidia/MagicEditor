"""Smoke: construct shipped dialogs (N7)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PyQt6")
pytest.importorskip("pytestqt")

from magiceditor.i18n.translator import TranslatorManager
from magiceditor.ui.command_palette import CommandPaletteDialog
from magiceditor.ui.compare_dialog import CompareDialog
from magiceditor.ui.confirm_dialog import ConfirmDialog
from magiceditor.ui.find_dialog import FindDialog
from magiceditor.ui.first_run_dialog import FirstRunDialog
from magiceditor.ui.goto_line_dialog import GoToLineDialog
from magiceditor.ui.quick_open import QuickOpenDialog
from magiceditor.ui.settings_pages.graphics import GraphicsPage
from magiceditor.ui.sidebar import Sidebar
from magiceditor.ui.splash_screen import MagicSplash


@pytest.mark.ui
def test_confirm_and_first_run_construct(qtbot) -> None:
    dlg = ConfirmDialog(None, text="ok", buttons="yes_no")
    qtbot.addWidget(dlg)
    assert dlg.windowTitle()
    fr = FirstRunDialog()
    qtbot.addWidget(fr)
    assert fr.want_associations() is False


@pytest.mark.ui
def test_goto_line_and_palette_construct(qtbot) -> None:
    g = GoToLineDialog(10, 1)
    qtbot.addWidget(g)
    pal = CommandPaletteDialog([])
    qtbot.addWidget(pal)
    assert g is not None
    assert pal is not None


class _FindHost:
    def find_text(self, *args, **kwargs) -> bool:
        return False


@pytest.mark.ui
def test_find_dialog_match_count_uses_line_text(qtbot) -> None:
    """K6: match count walks line_text, not doc.text()/toPlainText()."""
    from magiceditor.core.document import Document
    from magiceditor.ui.find_dialog import FindDialog
    from magiceditor.ui.virtual_editor import VirtualEditor

    src = Path(__file__).resolve().parents[2] / "src" / "magiceditor" / "ui" / "find_dialog.py"
    body = src.read_text(encoding="utf-8")
    count_fn = body.split("def _on_find_text_changed", 1)[1].split("def _tt", 1)[0]
    assert "doc.text()" not in count_fn
    assert "toPlainText" not in count_fn
    assert "toPlainText" not in body
    assert "count_matches_in_lines" in count_fn

    ed = VirtualEditor(Document.from_text("hello\nhello\nworld"))
    qtbot.addWidget(ed)
    dlg = FindDialog(ed)
    qtbot.addWidget(dlg)
    dlg.find_input.setText("hello")
    assert "2" in dlg._status.text()


@pytest.mark.ui
def test_find_compare_sidebar_splash_construct(qtbot) -> None:
    fd = FindDialog(_FindHost())
    qtbot.addWidget(fd)
    cd = CompareDialog("a", "left", "b", "right")
    qtbot.addWidget(cd)
    side = Sidebar()
    qtbot.addWidget(side)
    splash = MagicSplash()
    qtbot.addWidget(splash)
    assert fd.windowTitle()
    assert side._model.rootPath() in {"", side._model.rootPath()}


@pytest.mark.ui
def test_quick_open_graphics_translator_construct(qtbot, tmp_path) -> None:
    qo = QuickOpenDialog(tmp_path)
    qtbot.addWidget(qo)
    from magiceditor.services.settings import SessionState

    page = GraphicsPage(SessionState(), lambda k, d: d)
    qtbot.addWidget(page)
    tr = TranslatorManager()
    tr.load("en_US")
    assert ".." not in tr.language
    assert qo is not None


class _TrHost:
    """Parent widget that exposes MainWindow's ``_tr`` for dialog titles."""

    def __init__(self, qtbot) -> None:
        from PyQt6.QtWidgets import QWidget

        self.widget = QWidget()
        qtbot.addWidget(self.widget)
        tr = TranslatorManager()
        tr.load("pt_BR")
        self.widget._tr = tr  # type: ignore[attr-defined]


@pytest.mark.ui
def test_compare_goto_performance_titles_use_locales(qtbot) -> None:
    """Leftover EN window titles go through translator keys."""
    from magiceditor.services.performance_info import PerformanceSnapshot
    from magiceditor.ui.goto_anything import GotoAnythingDialog
    from magiceditor.ui.performance_dialog import PerformanceDialog

    host = _TrHost(qtbot).widget
    cd = CompareDialog("a", "L", "b", "R", host)
    qtbot.addWidget(cd)
    assert cd.windowTitle() == "Comparar"

    ga = GotoAnythingDialog(files=[], symbols=[], parent=host)
    qtbot.addWidget(ga)
    assert ga.windowTitle() == "Ir para qualquer coisa"

    snap = PerformanceSnapshot(
        python="3",
        platform="win",
        line_count=1,
        buffer_bytes=1,
        huge_mode=False,
        mmap_active=False,
        gpu_hint="off",
        portable=False,
        spell_enabled=False,
    )
    pd = PerformanceDialog(snap, host)
    qtbot.addWidget(pd)
    assert pd.windowTitle() == "Desempenho"
