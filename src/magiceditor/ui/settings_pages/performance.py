"""Performance settings page (J1.4)."""

from __future__ import annotations

from PyQt6.QtWidgets import QCheckBox, QFormLayout, QGroupBox, QSpinBox, QVBoxLayout, QWidget

from magiceditor.services.settings import SessionState
from magiceditor.ui.settings_pages.common import Translate, hint_label, wrap_scroll

PAGE_ID = "performance"


class PerformancePage(QWidget):
    def __init__(self, state: SessionState, t: Translate, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.setSpacing(14)

        g = QGroupBox(t("settings.perf_group", "Desempenho e extras"), page)
        form = QFormLayout(g)
        form.setSpacing(8)
        form.setContentsMargins(12, 16, 12, 12)

        self.minimap_box = QCheckBox(t("settings.minimap", "Mostrar minimap"), g)
        self.minimap_box.setChecked(bool(state.show_minimap))
        form.addRow(self.minimap_box)

        self.autosave_spin = QSpinBox(g)
        self.autosave_spin.setRange(0, 3600)
        self.autosave_spin.setSuffix(" s")
        self.autosave_spin.setSpecialValueText(t("settings.autosave_off", "Desligado"))
        self.autosave_spin.setValue(int(state.autosave_interval_sec or 0))
        form.addRow(t("settings.autosave", "Autosave"), self.autosave_spin)
        form.addRow(
            hint_label(
                t(
                    "settings.perf_hint",
                    "Arquivos grandes usam mmap + viewport automático. "
                    "Ortografia e realce atuam só na área visível. "
                    "Minimap e autosave podem aumentar o uso de CPU em "
                    "documentos muito grandes.",
                ),
                g,
            )
        )
        lay.addWidget(g)
        lay.addStretch(1)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(wrap_scroll(self, page))

    def apply(self, state: SessionState) -> None:
        state.show_minimap = self.minimap_box.isChecked()
        state.autosave_interval_sec = int(self.autosave_spin.value())
