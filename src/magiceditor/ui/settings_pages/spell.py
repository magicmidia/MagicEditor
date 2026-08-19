"""Spell settings page (J1.4)."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from magiceditor.services.settings import SessionState
from magiceditor.ui.settings_pages.common import Translate, hint_label, wrap_scroll

PAGE_ID = "spell"


class SpellPage(QWidget):
    def __init__(
        self, state: SessionState, t: Translate, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.setSpacing(14)

        g = QGroupBox(t("settings.spell_group", "Correção ortográfica"), page)
        form = QFormLayout(g)
        form.setSpacing(8)
        form.setContentsMargins(12, 16, 12, 12)

        self.spell_box = QCheckBox(t("settings.spell_check", "Ativar ortografia"), g)
        self.spell_box.setChecked(bool(state.spell_check))
        form.addRow(self.spell_box)

        self.spell_all_box = QCheckBox(
            t(
                "settings.spell_all_files",
                "Aplicar a todos os tipos de arquivo (não só texto/markdown)",
            ),
            g,
        )
        self.spell_all_box.setChecked(state.spell_force is True)
        form.addRow(self.spell_all_box)

        self.spell_lang_box = QComboBox(g)
        for code, label in (
            ("pt_BR", "Português (Brasil)"),
            ("en_US", "English (US)"),
            ("es_ES", "Español"),
        ):
            self.spell_lang_box.addItem(label, code)
        sidx = self.spell_lang_box.findData(state.spell_language or "pt_BR")
        self.spell_lang_box.setCurrentIndex(max(0, sidx))
        form.addRow(t("settings.spell_language", "Idioma principal"), self.spell_lang_box)

        extras = (state.spell_extra_languages or "").replace(" ", "")
        extra_set = set(extras.split(",")) if extras else set()
        self.spell_en_box = QCheckBox("English (US) adicional", g)
        self.spell_en_box.setChecked("en_US" in extra_set)
        self.spell_es_box = QCheckBox("Español adicional", g)
        self.spell_es_box.setChecked("es_ES" in extra_set)
        self.spell_pt_box = QCheckBox("Português (Brasil) adicional", g)
        self.spell_pt_box.setChecked("pt_BR" in extra_set)
        form.addRow(t("settings.spell_extra", "Idiomas extras (união)"), QLabel(""))
        form.addRow(self.spell_pt_box)
        form.addRow(self.spell_en_box)
        form.addRow(self.spell_es_box)

        lay.addWidget(g)
        lay.addWidget(
            hint_label(
                t(
                    "settings.spell_hint",
                    "Por arquivo: clique em Spell na barra de status para "
                    "ativar/desativar idiomas. Idiomas extras formam união "
                    "de dicionários no padrão de novos arquivos.",
                ),
                page,
            )
        )
        lay.addStretch(1)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(wrap_scroll(self, page))

    def apply(self, state: SessionState) -> None:
        state.spell_check = self.spell_box.isChecked()
        state.spell_force = True if self.spell_all_box.isChecked() else None
        slang = self.spell_lang_box.currentData()
        state.spell_language = str(slang) if slang else "pt_BR"
        extras: list[str] = []
        primary = state.spell_language
        if self.spell_pt_box.isChecked() and primary != "pt_BR":
            extras.append("pt_BR")
        if self.spell_en_box.isChecked() and primary != "en_US":
            extras.append("en_US")
        if self.spell_es_box.isChecked() and primary != "es_ES":
            extras.append("es_ES")
        state.spell_extra_languages = ",".join(extras)
