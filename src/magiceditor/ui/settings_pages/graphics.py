"""Graphics settings page (J1.4)."""

from __future__ import annotations

from PyQt6.QtWidgets import QCheckBox, QGroupBox, QVBoxLayout, QWidget

from magiceditor.services.settings import SessionState
from magiceditor.ui.settings_pages.common import Translate, hint_label, wrap_scroll

PAGE_ID = "graphics"


class GraphicsPage(QWidget):
    def __init__(self, state: SessionState, t: Translate, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.setSpacing(14)

        gfx = QGroupBox(t("settings.graphics", "Aceleração gráfica"), page)
        gfx_form = QVBoxLayout(gfx)
        gfx_form.setSpacing(6)
        gfx_form.setContentsMargins(12, 16, 12, 12)

        self.gpu_box = QCheckBox(t("settings.gpu", "Aceleração por GPU (composição OpenGL)"), gfx)
        self.gpu_box.setChecked(state.gpu_acceleration)
        self.msaa_box = QCheckBox(t("settings.msaa", "Anti-aliasing multisample (MSAA 4x)"), gfx)
        self.msaa_box.setChecked(state.gpu_multisample)
        self.aa_box = QCheckBox(t("settings.aa", "Anti-aliasing de texto e interface"), gfx)
        self.aa_box.setChecked(state.antialiasing)
        self.gpu_box.toggled.connect(self.msaa_box.setEnabled)
        self.msaa_box.setEnabled(self.gpu_box.isChecked())
        gfx_form.addWidget(self.gpu_box)
        gfx_form.addWidget(self.msaa_box)
        gfx_form.addWidget(self.aa_box)
        gfx_form.addWidget(
            hint_label(
                t(
                    "settings.gpu_hint",
                    "Alterar GPU ou MSAA exige reiniciar o MagicEditor.",
                ),
                gfx,
            )
        )
        lay.addWidget(gfx)
        lay.addStretch(1)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(wrap_scroll(self, page))

    def apply(self, state: SessionState) -> None:
        state.gpu_acceleration = self.gpu_box.isChecked()
        state.gpu_multisample = self.msaa_box.isChecked()
        state.antialiasing = self.aa_box.isChecked()
