"""Deep settings dialog apply_to_state."""

from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from magiceditor.services.settings import SessionState
from magiceditor.ui.settings_dialog import SettingsDialog


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_settings_apply_tab_and_spell(qapp) -> None:
    state = SessionState()
    dlg = SettingsDialog(state, languages=["pt_BR", "en_US", "es_ES"])
    dlg.tab_height_spin.setValue(32)
    dlg.tab_min_spin.setValue(80)
    dlg.tab_max_spin.setValue(200)
    dlg.spell_box.setChecked(True)
    dlg.spell_en_box.setChecked(True)
    dlg.show_ws_box.setChecked(True)
    dlg.caret_width_spin.setValue(2)
    out = dlg.apply_to_state(state)
    assert out.tab_height == 32
    assert out.tab_min_width == 80
    assert out.tab_max_width == 200
    assert out.show_whitespace is True
    assert out.caret_width == 2
    assert "en_US" in (out.spell_extra_languages or "")
