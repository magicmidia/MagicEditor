"""Status bar: version (left), encoding, EOL, cursor, spell + sync accent."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QLabel, QStatusBar, QWidget

from magiceditor.version import version_label


class _ClickableLabel(QLabel):
    """Status segment that emits clicked (for spell language menu, etc.)."""

    clicked = pyqtSignal()

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if event is not None and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class EditorStatusBar(QStatusBar):
    spell_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # Bottom-left: product version (centralized source)
        self._version = QLabel(version_label())
        self._version.setObjectName("statusVersion")
        self._version.setToolTip(f"MagicEditor {version_label()}")
        self._sync = QLabel("Local only")
        self._sync.setObjectName("statusAccent")
        self._position = QLabel("Ln 1, Col 1")
        self._encoding = QLabel("UTF-8")
        self._eol = QLabel("LF")
        self._filetype = QLabel("TEXT")
        self._spell = _ClickableLabel("Spell —")
        self._spell.setToolTip("Clique para escolher idiomas do dicionário deste arquivo")
        self._spell.clicked.connect(self.spell_clicked.emit)
        self.addWidget(self._version)
        self.addWidget(self._sync, 1)
        for w in (self._spell, self._filetype, self._encoding, self._eol, self._position):
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

    def set_spell_status(self, enabled: bool, language: str = "") -> None:
        if enabled:
            self._spell.setText(f"Spell {language or 'ON'}")
        else:
            self._spell.setText("Spell OFF")

    def set_version_text(self, text: str | None = None) -> None:
        self._version.setText(text if text is not None else version_label())
