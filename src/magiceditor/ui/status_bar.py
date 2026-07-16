"""Status bar: encoding, EOL, cursor, file meta + sync accent."""

from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QStatusBar, QWidget


class EditorStatusBar(QStatusBar):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sync = QLabel("Sync Active: MagicCloud")
        self._sync.setObjectName("statusAccent")
        self._position = QLabel("Ln 1, Col 1")
        self._encoding = QLabel("UTF-8")
        self._eol = QLabel("LF")
        self._filetype = QLabel("TEXT")
        self.addWidget(self._sync, 1)
        for w in (self._filetype, self._encoding, self._eol, self._position):
            w.setMinimumWidth(56)
            self.addPermanentWidget(w)

    def set_cursor(self, line: int, column: int) -> None:
        self._position.setText(f"Ln {line}, Col {column}")

    def set_encoding(self, encoding: str) -> None:
        self._encoding.setText(encoding.upper().replace("UTF-8-SIG", "UTF-8 BOM"))

    def set_eol(self, eol: str) -> None:
        self._eol.setText(eol)

    def set_filetype(self, label: str) -> None:
        self._filetype.setText(label)

    def set_sync_message(self, text: str) -> None:
        self._sync.setText(text)
