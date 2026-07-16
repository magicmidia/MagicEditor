"""Settings dialog — graphics (GPU) and transparency."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from magiceditor.services.settings import SessionState


class SettingsDialog(QDialog):
    """Configure GPU acceleration and window/editor transparency."""

    def __init__(
        self,
        state: SessionState,
        parent: QWidget | None = None,
        *,
        tr: Any | None = None,
    ) -> None:
        super().__init__(parent)
        self._tr = tr
        self.setModal(True)
        self.setMinimumWidth(440)
        self.setObjectName("settingsDialog")

        def t(key: str, default: str) -> str:
            if self._tr is not None:
                return self._tr.t(key, default)
            return default

        self.setWindowTitle(t("settings.title", "Configurações"))

        self.gpu_box = QCheckBox(t("settings.gpu", "Aceleração por GPU (composição OpenGL)"), self)
        self.gpu_box.setChecked(state.gpu_acceleration)
        self.msaa_box = QCheckBox(t("settings.msaa", "Anti-aliasing multisample (MSAA 4x)"), self)
        self.msaa_box.setChecked(state.gpu_multisample)
        self.aa_box = QCheckBox(t("settings.aa", "Anti-aliasing de texto e interface"), self)
        self.aa_box.setChecked(state.antialiasing)
        self.gpu_box.toggled.connect(self._sync_gpu_deps)

        gpu_hint = QLabel(
            t(
                "settings.gpu_hint",
                "O modo GPU é configurado antes da inicialização. "
                "Alterar GPU ou MSAA exige reiniciar o MagicEditor.",
            ),
            self,
        )
        gpu_hint.setWordWrap(True)
        gpu_hint.setObjectName("findDialogStatus")

        gfx = QGroupBox(t("settings.graphics", "Aceleração gráfica"), self)
        gfx_form = QVBoxLayout(gfx)
        gfx_form.setSpacing(6)
        gfx_form.setContentsMargins(10, 14, 10, 10)
        gfx_form.addWidget(self.gpu_box)
        gfx_form.addWidget(self.msaa_box)
        gfx_form.addWidget(self.aa_box)
        gfx_form.addWidget(gpu_hint)

        self.chrome_box = QCheckBox(
            t("settings.chrome", "Chrome translúcido (efeito vidro)"), self
        )
        self.chrome_box.setChecked(state.chrome_transparency)
        self.editor_box = QCheckBox(
            t("settings.editor_alpha", "Editor translúcido"), self
        )
        self.editor_box.setChecked(state.editor_transparency)

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.opacity_slider.setRange(55, 100)
        self.opacity_slider.setValue(round(state.window_opacity * 100))
        self.opacity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.opacity_slider.setTickInterval(5)
        self.opacity_label = QLabel(self._opacity_text(), self)
        self.opacity_slider.valueChanged.connect(self._on_opacity)

        opac_row = QHBoxLayout()
        opac_row.setSpacing(8)
        opac_row.addWidget(QLabel(t("settings.opacity", "Opacidade da janela"), self))
        opac_row.addWidget(self.opacity_slider, 1)
        opac_row.addWidget(self.opacity_label)

        vis = QGroupBox(t("settings.transparency", "Transparência"), self)
        vis_form = QVBoxLayout(vis)
        vis_form.setSpacing(6)
        vis_form.setContentsMargins(10, 14, 10, 10)
        vis_form.addLayout(opac_row)
        vis_form.addWidget(self.chrome_box)
        vis_form.addWidget(self.editor_box)
        tip = QLabel(
            t(
                "settings.opacity_hint",
                "Opacidade e vidro aplicam-se imediatamente. "
                "No Windows, o desfoque acrylic completo é limitado.",
            ),
            self,
        )
        tip.setWordWrap(True)
        tip.setObjectName("findDialogStatus")
        vis_form.addWidget(tip)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        cancel_btn = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if ok_btn is not None:
            ok_btn.setText(t("dialog.ok", "OK"))
        if cancel_btn is not None:
            cancel_btn.setText(t("dialog.cancel", "Cancelar"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)
        root.addWidget(gfx)
        root.addWidget(vis)
        root.addWidget(buttons)

        QShortcut(QKeySequence("Esc"), self, activated=self.reject)
        self._sync_gpu_deps(self.gpu_box.isChecked())

    def _opacity_text(self) -> str:
        return f"{self.opacity_slider.value()}%"

    def _on_opacity(self, _v: int) -> None:
        self.opacity_label.setText(self._opacity_text())

    def _sync_gpu_deps(self, enabled: bool) -> None:
        self.msaa_box.setEnabled(enabled)

    def apply_to_state(self, state: SessionState) -> SessionState:
        """Mutate and return ``state`` with dialog values."""
        state.gpu_acceleration = self.gpu_box.isChecked()
        state.gpu_multisample = self.msaa_box.isChecked()
        state.antialiasing = self.aa_box.isChecked()
        state.window_opacity = self.opacity_slider.value() / 100.0
        state.chrome_transparency = self.chrome_box.isChecked()
        state.editor_transparency = self.editor_box.isChecked()
        return state
