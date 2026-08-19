from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")
pytest.importorskip("pytestqt")

from PyQt6.QtWidgets import QLabel

from magiceditor.themes.tokens import chrome_tokens
from magiceditor.ui.about_dialog import AboutDialog


@pytest.mark.ui
def test_about_rich_text_uses_theme_foreground(qtbot) -> None:
    dlg = AboutDialog(theme_id="luminous_void")
    qtbot.addWidget(dlg)
    tok = chrome_tokens("luminous_void")
    about_body = next(lab for lab in dlg.findChildren(QLabel) if lab.objectName() == "aboutBody")
    assert tok.fg.lower() in about_body.text().lower()
    assert about_body.palette().windowText().color().name().lower() == tok.fg.lower()
