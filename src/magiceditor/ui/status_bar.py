"""Status bar: encoding, EOL, cursor, file size."""

from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QStatusBar, QWidget


class EditorStatusBar(QStatusBar):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._meta = QLabel("Ready")
        self.addPermanentWidget(self._meta)

    def set_meta(self, text: str) -> None:
        self._meta.setText(text)
