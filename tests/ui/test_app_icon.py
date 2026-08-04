"""Application icon asset exists and loads as QIcon."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("PyQt6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from magiceditor.paths import app_icon_path
from magiceditor.ui.app_icon import load_app_icon


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_app_icon_file_exists() -> None:
    path = app_icon_path()
    assert path.is_file(), f"missing app icon: {path}"
    assert path.suffix.lower() == ".ico"
    assert path.stat().st_size > 100


def test_load_app_icon(qapp) -> None:
    ico = load_app_icon()
    assert not ico.isNull()
    sizes = ico.availableSizes()
    assert sizes, "icon should expose at least one size"
