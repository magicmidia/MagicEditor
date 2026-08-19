"""General settings page (J1.4)."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from magiceditor.services.settings import SessionState
from magiceditor.ui.settings_pages.common import Translate, hint_label, wrap_scroll

PAGE_ID = "general"
PAGE_TITLE_KEY = "settings.tab.general"


class GeneralPage(QWidget):
    def __init__(
        self,
        state: SessionState,
        t: Translate,
        languages: list[str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.setSpacing(14)

        g = QGroupBox(t("settings.general_group", "Geral"), page)
        form = QFormLayout(g)
        form.setSpacing(8)
        form.setContentsMargins(12, 16, 12, 12)

        self.lang_box = QComboBox(g)
        lang_labels = {
            "pt_BR": t("lang.pt_BR", "Português (Brasil)"),
            "en_US": t("lang.en_US", "English (US)"),
            "es_ES": t("lang.es_ES", "Español"),
        }
        for code in languages:
            self.lang_box.addItem(lang_labels.get(code, code), code)
        idx = self.lang_box.findData(state.language or "pt_BR")
        self.lang_box.setCurrentIndex(max(0, idx))
        form.addRow(t("settings.language", "Idioma"), self.lang_box)

        self.restore_session_box = QCheckBox(
            t("settings.restore_session", "Restaurar abas e rascunhos ao iniciar"), g
        )
        self.restore_session_box.setChecked(state.restore_session)
        form.addRow(self.restore_session_box)

        self.open_in_existing_box = QCheckBox(
            t(
                "settings.open_in_existing",
                "Abrir arquivos no editor já aberto (nova aba)",
            ),
            g,
        )
        self.open_in_existing_box.setChecked(bool(state.open_in_existing_window))
        form.addRow(self.open_in_existing_box)

        self.show_toolbar_box = QCheckBox(
            t("settings.show_toolbar", "Mostrar barra de ferramentas"), g
        )
        self.show_toolbar_box.setChecked(state.show_toolbar)
        form.addRow(self.show_toolbar_box)

        self.show_status_box = QCheckBox(
            t("settings.show_status_bar", "Mostrar barra de status"), g
        )
        self.show_status_box.setChecked(state.show_status_bar)
        form.addRow(self.show_status_box)

        self.recent_max_spin = QSpinBox(g)
        self.recent_max_spin.setRange(5, 50)
        self.recent_max_spin.setValue(int(state.recent_files_max or 15))
        form.addRow(t("settings.recent_max", "Máx. arquivos recentes"), self.recent_max_spin)

        self.context_menu_box = QCheckBox(
            t("settings.editor_context_menu", "Menu de contexto no editor (botão direito)"),
            g,
        )
        self.context_menu_box.setChecked(bool(state.editor_context_menu))
        form.addRow(self.context_menu_box)

        self.splash_box = QCheckBox(
            t("settings.show_splash", "Mostrar tela inicial (splash) ao abrir — mínimo 1,5 s"),
            g,
        )
        self.splash_box.setChecked(bool(state.show_splash))
        form.addRow(self.splash_box)

        lay.addWidget(g)
        lay.addWidget(
            hint_label(
                t(
                    "settings.general_hint",
                    "Idioma e restauração de sessão aplicam-se ao confirmar.",
                ),
                page,
            )
        )
        lay.addStretch(1)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(wrap_scroll(self, page))

    def apply(self, state: SessionState) -> None:
        lang = self.lang_box.currentData()
        state.language = str(lang) if lang else state.language
        state.restore_session = self.restore_session_box.isChecked()
        state.open_in_existing_window = self.open_in_existing_box.isChecked()
        state.show_toolbar = self.show_toolbar_box.isChecked()
        state.show_status_bar = self.show_status_box.isChecked()
        state.recent_files_max = int(self.recent_max_spin.value())
        state.editor_context_menu = self.context_menu_box.isChecked()
        state.show_splash = self.splash_box.isChecked()
