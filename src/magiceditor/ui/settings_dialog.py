"""Settings dialog — graphics (GPU) and transparency."""

from __future__ import annotations

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

    def __init__(self, state: SessionState, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(460)
        self.setObjectName("settingsDialog")

        # --- Graphics ---
        self.gpu_box = QCheckBox("GPU acceleration (OpenGL composition)", self)
        self.gpu_box.setChecked(state.gpu_acceleration)
        self.msaa_box = QCheckBox("Multisample anti-aliasing (4x MSAA)", self)
        self.msaa_box.setChecked(state.gpu_multisample)
        self.aa_box = QCheckBox("Text / UI anti-aliasing", self)
        self.aa_box.setChecked(state.antialiasing)
        self.gpu_box.toggled.connect(self._sync_gpu_deps)

        gpu_hint = QLabel(
            "GPU mode configures OpenGL before startup. "
            "Changing GPU or MSAA requires restarting MagicEditor.",
            self,
        )
        gpu_hint.setWordWrap(True)
        gpu_hint.setObjectName("findDialogStatus")

        gfx = QGroupBox("Graphics acceleration", self)
        gfx_form = QVBoxLayout(gfx)
        gfx_form.setSpacing(8)
        gfx_form.addWidget(self.gpu_box)
        gfx_form.addWidget(self.msaa_box)
        gfx_form.addWidget(self.aa_box)
        gfx_form.addWidget(gpu_hint)

        # --- Transparency ---
        self.chrome_box = QCheckBox("Translucent window chrome (glass)", self)
        self.chrome_box.setChecked(state.chrome_transparency)
        self.editor_box = QCheckBox("Translucent editor canvas", self)
        self.editor_box.setChecked(state.editor_transparency)

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.opacity_slider.setRange(55, 100)
        self.opacity_slider.setValue(round(state.window_opacity * 100))
        self.opacity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.opacity_slider.setTickInterval(5)
        self.opacity_label = QLabel(self._opacity_text(), self)
        self.opacity_slider.valueChanged.connect(self._on_opacity)

        opac_row = QHBoxLayout()
        opac_row.addWidget(QLabel("Window opacity", self))
        opac_row.addWidget(self.opacity_slider, 1)
        opac_row.addWidget(self.opacity_label)

        vis = QGroupBox("Transparency", self)
        vis_form = QVBoxLayout(vis)
        vis_form.setSpacing(8)
        vis_form.addLayout(opac_row)
        vis_form.addWidget(self.chrome_box)
        vis_form.addWidget(self.editor_box)
        tip = QLabel(
            "Opacity and glass apply immediately. "
            "On Windows, full acrylic blur is best-effort via translucent chrome + opacity.",
            self,
        )
        tip.setWordWrap(True)
        tip.setObjectName("findDialogStatus")
        vis_form.addWidget(tip)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)
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
