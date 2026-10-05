"""Design settings page (J1.4)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from magiceditor.services.settings import SessionState
from magiceditor.themes.manager import NATIVE_THEMES
from magiceditor.ui.icons import ICON_PACKS
from magiceditor.ui.settings_pages.common import Translate, wrap_scroll

PAGE_ID = "design"


class DesignPage(QWidget):
    def __init__(self, state: SessionState, t: Translate, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.setSpacing(14)

        theme_g = QGroupBox(t("settings.theme_group", "Tema e ícones"), page)
        form = QFormLayout(theme_g)
        form.setSpacing(8)
        form.setContentsMargins(12, 16, 12, 12)

        self.theme_box = QComboBox(theme_g)
        for tid, label in NATIVE_THEMES.items():
            self.theme_box.addItem(t(f"theme.{tid}", label), tid)
        idx = self.theme_box.findData(state.theme or "luminous_void")
        self.theme_box.setCurrentIndex(max(0, idx))
        form.addRow(t("settings.theme", "Tema visual"), self.theme_box)

        self.icon_pack_box = QComboBox(theme_g)
        current_pack = state.icon_pack or "qlementine"
        for pack_id, default_label in ICON_PACKS:
            if pack_id == "qlementine":
                label = t("settings.icon_pack_qlementine", "Qlementine (Qt)")
            elif pack_id == "material":
                label = t("settings.icon_pack_material", "Material Design (outline / light)")
            else:
                label = default_label
            self.icon_pack_box.addItem(label, pack_id)
        pidx = self.icon_pack_box.findData(current_pack)
        self.icon_pack_box.setCurrentIndex(max(0, pidx))
        form.addRow(t("settings.icon_pack", "Pacote de ícones"), self.icon_pack_box)
        lay.addWidget(theme_g)

        vis = QGroupBox(t("settings.transparency", "Transparência"), page)
        vis_form = QVBoxLayout(vis)
        vis_form.setSpacing(6)
        vis_form.setContentsMargins(12, 16, 12, 12)

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal, vis)
        self.opacity_slider.setRange(55, 100)
        self.opacity_slider.setValue(round(state.window_opacity * 100))
        self.opacity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.opacity_slider.setTickInterval(5)
        self.opacity_label = QLabel(f"{self.opacity_slider.value()}%", vis)
        self.opacity_slider.valueChanged.connect(self._on_opacity)
        opac_row = QHBoxLayout()
        opac_row.addWidget(QLabel(t("settings.opacity", "Opacidade da janela"), vis))
        opac_row.addWidget(self.opacity_slider, 1)
        opac_row.addWidget(self.opacity_label)
        vis_form.addLayout(opac_row)

        self.chrome_box = QCheckBox(t("settings.chrome", "Chrome translúcido (efeito vidro)"), vis)
        self.chrome_box.setChecked(state.chrome_transparency)
        vis_form.addWidget(self.chrome_box)
        self.editor_box = QCheckBox(t("settings.editor_alpha", "Editor translúcido"), vis)
        self.editor_box.setChecked(state.editor_transparency)
        vis_form.addWidget(self.editor_box)
        lay.addWidget(vis)
        lay.addStretch(1)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(wrap_scroll(self, page))

    def _on_opacity(self, _v: int) -> None:
        self.opacity_label.setText(f"{self.opacity_slider.value()}%")

    def apply(self, state: SessionState) -> None:
        theme = self.theme_box.currentData()
        state.theme = str(theme) if theme else state.theme
        pack = self.icon_pack_box.currentData()
        state.icon_pack = str(pack) if pack else "qlementine"
        state.window_opacity = self.opacity_slider.value() / 100.0
        state.chrome_transparency = self.chrome_box.isChecked()
        state.editor_transparency = self.editor_box.isChecked()
