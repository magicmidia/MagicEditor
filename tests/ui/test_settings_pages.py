"""J1.4: one settings page per module; dialog is a shell."""

from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from magiceditor.services.settings import SessionState
from magiceditor.ui.settings_dialog import SettingsDialog
from magiceditor.ui.settings_pages.design import DesignPage
from magiceditor.ui.settings_pages.editor import EditorPage
from magiceditor.ui.settings_pages.general import GeneralPage
from magiceditor.ui.settings_pages.graphics import GraphicsPage
from magiceditor.ui.settings_pages.performance import PerformancePage
from magiceditor.ui.settings_pages.spell import SpellPage
from magiceditor.ui.settings_pages.tabs import TabsPage


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_general_page_apply_writes_language(qapp) -> None:
    """J1.4: GeneralPage.apply is the shipped path into SessionState."""
    state = SessionState(language="pt_BR")

    def t(key: str, default: str) -> str:
        return default

    page = GeneralPage(state, t, ["pt_BR", "en_US"])
    idx = page.lang_box.findData("en_US")
    assert idx >= 0
    page.lang_box.setCurrentIndex(idx)
    page.restore_session_box.setChecked(False)
    page.open_in_existing_box.setChecked(False)
    page.apply(state)
    assert state.language == "en_US"
    assert state.restore_session is False
    assert state.open_in_existing_window is False


def test_each_page_module_applies(qapp) -> None:
    state = SessionState()

    def t(key: str, default: str) -> str:
        return default

    pages = [
        GeneralPage(state, t, ["pt_BR", "en_US"]),
        EditorPage(state, t),
        SpellPage(state, t),
        DesignPage(state, t),
        GraphicsPage(state, t),
        TabsPage(state, t),
        PerformancePage(state, t),
    ]
    for page in pages:
        qtbot = qapp
        assert qtbot is not None
        page.apply(state)
    assert state.language == "pt_BR"
    assert state.tab_width >= 2


def test_dialog_shell_delegates_apply(qapp) -> None:
    state = SessionState()
    dlg = SettingsDialog(state, languages=["pt_BR", "en_US", "es_ES"])
    assert dlg.stack.count() == 7
    assert all(hasattr(p, "apply") for p in dlg._pages)
    dlg.tab_height_spin.setValue(32)
    dlg.spell_box.setChecked(True)
    dlg.spell_en_box.setChecked(True)
    out = dlg.apply_to_state(state)
    assert out.tab_height == 32
    assert "en_US" in (out.spell_extra_languages or "")
