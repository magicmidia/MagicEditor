"""File explorer dock."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import QTreeView, QWidget


class Sidebar(QTreeView):
    """Project/file tree; double-click emits file path."""

    file_activated = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model = QFileSystemModel(self)
        self._model.setRootPath("")
        self.setModel(self._model)
        self.setRootIndex(self._model.index(str(Path.home())))
        # Hide size/type/date columns for a cleaner explorer
        for col in range(1, 4):
            self.hideColumn(col)
        self.doubleClicked.connect(self._on_double_clicked)

    def set_root_path(self, path: str | Path) -> None:
        path = str(path)
        self._model.setRootPath(path)
        self.setRootIndex(self._model.index(path))

    def _on_double_clicked(self, index) -> None:
        path = self._model.filePath(index)
        if path and not self._model.isDir(index):
            self.file_activated.emit(path)
