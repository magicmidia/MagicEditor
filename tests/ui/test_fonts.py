"""Cascadia Code font loading (requires Qt app)."""

from __future__ import annotations

import sys

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from magiceditor.ui.fonts import editor_font, font_family, load_bundled_fonts, ui_font


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app  # type: ignore[return-value]


@pytest.mark.ui
def test_bundled_cascadia_loads(qapp: QApplication) -> None:
    family = load_bundled_fonts()
    assert family
    assert "cascadia" in family.lower() or family == "Cascadia Code"
    ui = ui_font(10)
    ed = editor_font(12)
    assert ui.pointSize() == 10
    assert ed.pointSize() == 12
    assert font_family()
    assert "cascadia" in ui.family().lower() or ui.family()
