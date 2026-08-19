"""Tabs settings page (J1.4)."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from magiceditor.services.settings import SessionState
from magiceditor.ui.settings_pages.common import Translate, wrap_scroll

PAGE_ID = "tabs"


class TabsPage(QWidget):
    def __init__(
        self, state: SessionState, t: Translate, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.setSpacing(14)

        g = QGroupBox(t("settings.tabs_chrome", "Aparência das abas"), page)
        form = QFormLayout(g)
        form.setSpacing(8)
        form.setContentsMargins(12, 16, 12, 12)

        self.tab_height_spin = QSpinBox(g)
        self.tab_height_spin.setRange(22, 40)
        self.tab_height_spin.setSuffix(" px")
        self.tab_height_spin.setValue(int(state.tab_height or 28))
        form.addRow(t("settings.tab_height", "Altura da aba"), self.tab_height_spin)

        self.tab_min_spin = QSpinBox(g)
        self.tab_min_spin.setRange(48, 160)
        self.tab_min_spin.setSuffix(" px")
        self.tab_min_spin.setValue(int(state.tab_min_width or 72))
        form.addRow(t("settings.tab_min_width", "Largura mínima"), self.tab_min_spin)

        self.tab_max_spin = QSpinBox(g)
        self.tab_max_spin.setRange(120, 400)
        self.tab_max_spin.setSuffix(" px")
        self.tab_max_spin.setValue(int(state.tab_max_width or 220))
        form.addRow(t("settings.tab_max_width", "Largura máxima"), self.tab_max_spin)
        lay.addWidget(g)

        beh = QGroupBox(t("settings.tabs_group", "Comportamento"), page)
        bform = QFormLayout(beh)
        bform.setSpacing(8)
        bform.setContentsMargins(12, 16, 12, 12)

        self.tab_scroll_box = QCheckBox(
            t("settings.tab_scroll_buttons", "Botões de navegação ◀ ▶"), beh
        )
        self.tab_scroll_box.setChecked(bool(state.show_tab_scroll_buttons))
        bform.addRow(self.tab_scroll_box)

        self.middle_close_box = QCheckBox(
            t("settings.middle_click_close", "Clique do meio fecha a aba"), beh
        )
        self.middle_close_box.setChecked(bool(state.middle_click_close))
        bform.addRow(self.middle_close_box)

        self.confirm_close_box = QCheckBox(
            t("settings.confirm_close_unsaved", "Perguntar ao fechar aba com alterações"),
            beh,
        )
        self.confirm_close_box.setChecked(bool(state.confirm_close_unsaved))
        bform.addRow(self.confirm_close_box)

        info = QLabel(
            t(
                "settings.tabs_info",
                "• Duplo clique na área vazia → novo arquivo\n"
                "• Botão + → novo arquivo\n"
                "• Arraste abas para reordenar\n"
                "• Clique direito → grupos de abas",
            ),
            beh,
        )
        info.setWordWrap(True)
        bform.addRow(info)
        lay.addWidget(beh)
        lay.addStretch(1)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(wrap_scroll(self, page))

    def apply(self, state: SessionState) -> None:
        state.tab_height = int(self.tab_height_spin.value())
        state.tab_min_width = int(self.tab_min_spin.value())
        state.tab_max_width = max(int(self.tab_max_spin.value()), state.tab_min_width)
        state.show_tab_scroll_buttons = self.tab_scroll_box.isChecked()
        state.middle_click_close = self.middle_close_box.isChecked()
        state.confirm_close_unsaved = self.confirm_close_box.isChecked()
