"""Virtual viewport text widget (placeholder)."""

from __future__ import annotations

from PyQt6.QtWidgets import QPlainTextEdit, QWidget


class TextEditor(QPlainTextEdit):
    """Temporary editor surface.

    Replace with virtual viewport bound to ``PieceTable`` for huge files.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
