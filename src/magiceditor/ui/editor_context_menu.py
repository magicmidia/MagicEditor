"""Right-click context menu for the editor viewport (edit + spell actions)."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import QMenu, QWidget


def _t(tr: Any | None, key: str, default: str) -> str:
    if tr is not None and hasattr(tr, "t"):
        return tr.t(key, default)
    return default


def build_editor_context_menu(
    parent: QWidget,
    *,
    tr: Any | None = None,
    has_selection: bool = False,
    can_undo: bool = True,
    can_redo: bool = True,
    can_paste: bool = True,
    read_only: bool = False,
    on_undo: Callable[[], None] | None = None,
    on_redo: Callable[[], None] | None = None,
    on_cut: Callable[[], None] | None = None,
    on_copy: Callable[[], None] | None = None,
    on_paste: Callable[[], None] | None = None,
    on_select_all: Callable[[], None] | None = None,
    on_find: Callable[[], None] | None = None,
    on_replace: Callable[[], None] | None = None,
    on_goto: Callable[[], None] | None = None,
    on_toggle_comment: Callable[[], None] | None = None,
    on_indent: Callable[[], None] | None = None,
    on_unindent: Callable[[], None] | None = None,
    # Spell / corrector
    spell_word: str | None = None,
    spell_misspelled: bool = False,
    spell_suggestions: Sequence[str] | None = None,
    on_spell_suggestion: Callable[[str], None] | None = None,
    on_spell_ignore: Callable[[], None] | None = None,
    on_spell_add: Callable[[], None] | None = None,
    on_command_palette: Callable[[], None] | None = None,
) -> QMenu:
    """Build a Chrome/VS Code-like editor context menu with spell section."""
    menu = QMenu(parent)
    t = lambda k, d: _t(tr, k, d)  # noqa: E731

    def add(
        label: str,
        slot: Callable[[], None] | None,
        *,
        enabled: bool = True,
    ) -> QAction:
        act = menu.addAction(label)
        act.setEnabled(bool(enabled and slot is not None))
        if slot is not None and enabled:
            act.triggered.connect(slot)
        return act

    # --- Spell corrector (top, when there is a word under the caret) ------
    word = (spell_word or "").strip()
    if word and (
        on_spell_ignore is not None or on_spell_add is not None or on_spell_suggestion is not None
    ):
        header = menu.addAction(t("spell.word_header", "Ortografia: “{w}”").format(w=word))
        header.setEnabled(False)
        hf = QFont(header.font())
        hf.setBold(True)
        header.setFont(hf)

        if spell_misspelled:
            suggestions = list(spell_suggestions or [])
            if suggestions and on_spell_suggestion is not None and not read_only:
                for sug in suggestions:
                    act = menu.addAction(t("spell.suggestion", "→ {s}").format(s=sug))
                    act.triggered.connect(lambda _checked=False, s=sug: on_spell_suggestion(s))
            else:
                none = menu.addAction(t("spell.no_suggestions", "(sem sugestões)"))
                none.setEnabled(False)
        else:
            ok = menu.addAction(t("spell.word_ok", "Palavra reconhecida"))
            ok.setEnabled(False)

        menu.addSeparator()
        if on_spell_ignore is not None:
            add(t("action.spell_ignore", "Ignorar palavra"), on_spell_ignore)
        if on_spell_add is not None:
            add(
                t("action.spell_add", "Adicionar ao dicionário"),
                on_spell_add,
            )
        menu.addSeparator()

    # --- Edit ----------------------------------------------------------
    ro = read_only
    add(t("action.undo", "Desfazer"), on_undo, enabled=can_undo and not ro)
    add(t("action.redo", "Refazer"), on_redo, enabled=can_redo and not ro)
    menu.addSeparator()
    add(t("action.cut", "Recortar"), on_cut, enabled=has_selection and not ro)
    act_copy = menu.addAction(t("action.copy", "Copiar"))
    act_copy.setEnabled(has_selection and on_copy is not None)
    if on_copy is not None:
        act_copy.triggered.connect(on_copy)
    add(t("action.paste", "Colar"), on_paste, enabled=can_paste and not ro)
    act_all = menu.addAction(t("action.select_all", "Selecionar tudo"))
    act_all.setEnabled(on_select_all is not None)
    if on_select_all is not None:
        act_all.triggered.connect(on_select_all)
    menu.addSeparator()

    if on_indent is not None or on_unindent is not None or on_toggle_comment is not None:
        add(t("action.indent", "Avançar indentação"), on_indent, enabled=not ro)
        add(t("action.unindent", "Recuar indentação"), on_unindent, enabled=not ro)
        if on_toggle_comment is not None:
            add(
                t("action.toggle_comment", "Alternar comentário"),
                on_toggle_comment,
                enabled=not ro,
            )
        menu.addSeparator()

    if on_find is not None or on_replace is not None or on_goto is not None:
        add(t("action.find", "Localizar"), on_find, enabled=on_find is not None)
        add(t("action.replace", "Substituir"), on_replace, enabled=on_replace is not None)
        add(t("action.goto_line", "Ir para linha…"), on_goto, enabled=on_goto is not None)
        menu.addSeparator()

    if on_command_palette is not None:
        add(t("action.command_palette", "Paleta de comandos"), on_command_palette)

    return menu
