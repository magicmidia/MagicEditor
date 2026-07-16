"""File explorer dock (placeholder)."""

from __future__ import annotations

from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import QTreeView, QWidget


class Sidebar(QTreeView):
    """Project/file tree; hide via Ctrl+B / F11 in later UI work."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model = QFileSystemModel(self)
        self.setModel(self._model)
