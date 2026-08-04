"""Editor context menu builder (offscreen)."""

from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication, QWidget

from magiceditor.ui.editor_context_menu import build_editor_context_menu


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_context_menu_has_edit_actions(qapp) -> None:
    parent = QWidget()
    calls: list[str] = []
    menu = build_editor_context_menu(
        parent,
        has_selection=True,
        can_undo=True,
        can_paste=True,
        on_cut=lambda: calls.append("cut"),
        on_copy=lambda: calls.append("copy"),
        on_paste=lambda: calls.append("paste"),
        on_select_all=lambda: calls.append("all"),
    )
    labels = [a.text() for a in menu.actions() if a.text()]
    assert any("Copiar" in x or "Copy" in x for x in labels)
    assert any("Colar" in x or "Paste" in x for x in labels)
    assert any("Recortar" in x or "Cut" in x for x in labels)


def test_cut_disabled_without_selection(qapp) -> None:
    parent = QWidget()
    menu = build_editor_context_menu(
        parent,
        has_selection=False,
        on_cut=lambda: None,
        on_copy=lambda: None,
        on_paste=lambda: None,
    )
    cut_acts = [
        a for a in menu.actions() if a.text() and ("Recortar" in a.text() or "Cut" in a.text())
    ]
    assert cut_acts
    assert not cut_acts[0].isEnabled()


def test_spell_section_with_suggestions(qapp) -> None:
    parent = QWidget()
    chosen: list[str] = []
    menu = build_editor_context_menu(
        parent,
        spell_word="helo",
        spell_misspelled=True,
        spell_suggestions=["hello", "help"],
        on_spell_suggestion=chosen.append,
        on_spell_ignore=lambda: None,
        on_spell_add=lambda: None,
    )
    texts = [a.text() for a in menu.actions() if a.text()]
    assert any("helo" in x for x in texts)
    assert any("hello" in x for x in texts)
    assert any("Ignorar" in x or "Ignore" in x for x in texts)
    assert any("dicionário" in x or "dictionary" in x.lower() for x in texts)
