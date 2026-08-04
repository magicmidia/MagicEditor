"""First-run onboarding: language + theme (+ optional associations note)."""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from magiceditor.themes.manager import NATIVE_THEMES


class FirstRunDialog(QDialog):
    def __init__(
        self,
        *,
        language: str = "pt_BR",
        theme: str = "luminous_void",
        tr: Any | None = None,
        languages: list[str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tr = tr

        def t(key: str, default: str) -> str:
            if self._tr is not None:
                return self._tr.t(key, default)
            return default

        self.setWindowTitle(t("first_run.title", "Welcome to MagicEditor"))
        self.setModal(True)
        self.resize(420, 280)

        title = QLabel(t("first_run.heading", "Choose your language and theme"))
        title.setWordWrap(True)

        form = QFormLayout()
        self.lang_box = QComboBox(self)
        langs = languages or ["pt_BR", "en_US", "es_ES"]
        labels = {
            "pt_BR": t("lang.pt_BR", "Português (Brasil)"),
            "en_US": t("lang.en_US", "English (US)"),
            "es_ES": t("lang.es_ES", "Español"),
        }
        for code in langs:
            self.lang_box.addItem(labels.get(code, code), code)
        idx = self.lang_box.findData(language)
        self.lang_box.setCurrentIndex(max(0, idx))
        form.addRow(t("first_run.language", "Interface language"), self.lang_box)

        self.theme_box = QComboBox(self)
        for tid, label in NATIVE_THEMES.items():
            self.theme_box.addItem(t(f"theme.{tid}", label), tid)
        tidx = self.theme_box.findData(theme)
        self.theme_box.setCurrentIndex(max(0, tidx))
        form.addRow(t("first_run.theme", "Theme"), self.theme_box)

        self.assoc_box = QCheckBox(
            t(
                "first_run.assoc",
                "Prefer MagicEditor for text files (set via installer / OS Settings)",
            ),
            self,
        )
        self.assoc_box.setChecked(True)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)

        root = QVBoxLayout(self)
        root.addWidget(title)
        root.addLayout(form)
        root.addWidget(self.assoc_box)
        root.addStretch(1)
        root.addWidget(buttons)

    def selected_language(self) -> str:
        data = self.lang_box.currentData()
        return str(data) if data else "pt_BR"

    def selected_theme(self) -> str:
        data = self.theme_box.currentData()
        return str(data) if data else "luminous_void"

    def want_associations(self) -> bool:
        return self.assoc_box.isChecked()
