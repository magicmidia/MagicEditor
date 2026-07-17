"""Icon pack switching (requires Qt)."""

from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")
pytest.importorskip("pytestqt")

from magiceditor.ui import icons as iconmod


@pytest.mark.ui
def test_qlementine_pack_has_svgs(qtbot) -> None:
    iconmod.set_icon_pack("qlementine")
    assert iconmod.get_icon_pack() == "qlementine"
    idx = iconmod._qlementine_index()
    assert len(idx) > 100
    ico = iconmod.icon("save", "#cccccc")
    assert not ico.isNull()


@pytest.mark.ui
def test_material_pack_icon(qtbot) -> None:
    iconmod.set_icon_pack("material")
    ico = iconmod.icon("find", "#888888")
    assert not ico.isNull()
    lang = iconmod.language_icon("python", "#888888")
    assert not lang.isNull()
    iconmod.set_icon_pack("qlementine")


@pytest.mark.ui
def test_language_icon_qlementine(qtbot) -> None:
    iconmod.set_icon_pack("qlementine")
    for lang in ("python", "markdown", "html", "text"):
        ico = iconmod.language_icon(lang, "#aaaaaa")
        assert not ico.isNull()
