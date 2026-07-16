"""Find in Files — search workspace folder for a literal string."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from magiceditor.services.folder_search import SearchHit, search_folder


class FindInFilesDialog(QDialog):
    """Modal folder search. Emits ``hit_activated(path, line, column)`` on open."""

    hit_activated = pyqtSignal(str, int, int)  # path, line (1-based), column (1-based)

    def __init__(
        self,
        root: Path | str | None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._root = Path(root) if root else None
        self.setModal(True)
        self.setWindowTitle("Find in Files")
        self.setMinimumSize(560, 420)
        self.setObjectName("findInFilesDialog")

        self.find_input = QLineEdit(self)
        self.find_input.setPlaceholderText("Search in workspace…")
        self.case_box = QCheckBox("Match case", self)
        self._status = QLabel("", self)
        self._status.setObjectName("findDialogStatus")
        self._results = QListWidget(self)
        self._results.setObjectName("findInFilesResults")
        self._results.itemDoubleClicked.connect(self._open_item)
        self._results.itemActivated.connect(self._open_item)

        btn_search = QPushButton("Search", self)
        btn_search.setDefault(True)
        btn_search.clicked.connect(self.run_search)
        btn_close = QPushButton("Close", self)
        btn_close.clicked.connect(self.reject)

        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self.find_input, 1)
        row.addWidget(self.case_box)
        row.addWidget(btn_search)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(btn_close)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)
        root_layout.addLayout(row)
        root_layout.addWidget(self._status)
        root_layout.addWidget(self._results, 1)
        root_layout.addLayout(buttons)

        self.find_input.returnPressed.connect(self.run_search)
        QShortcut(QKeySequence("Esc"), self, activated=self.reject)

        if self._root is None or not self._root.is_dir():
            self._status.setText("Open a folder (File → Open Folder) to search.")
            btn_search.setEnabled(False)
            self.find_input.setEnabled(False)
        else:
            self._status.setText(f"Workspace: {self._root}")
            self.find_input.setFocus()

    def run_search(self) -> None:
        if self._root is None or not self._root.is_dir():
            self._status.setText("No workspace folder open.")
            return
        needle = self.find_input.text()
        if not needle:
            self._status.setText("Enter text to find.")
            return

        self._results.clear()
        self._status.setText("Searching…")
        hits = search_folder(
            self._root,
            needle,
            case_sensitive=self.case_box.isChecked(),
        )
        if not hits:
            self._status.setText("No matches.")
            return

        try:
            root_resolved = self._root.resolve()
        except OSError:
            root_resolved = self._root

        for hit in hits:
            item = QListWidgetItem(self._format_hit(hit, root_resolved))
            item.setData(Qt.ItemDataRole.UserRole, hit)
            self._results.addItem(item)

        more = " (capped)" if len(hits) >= 200 else ""
        self._status.setText(f"{len(hits)} match(es){more}. Double-click to open.")

    def _format_hit(self, hit: SearchHit, root: Path) -> str:
        try:
            rel = hit.path.resolve().relative_to(root)
            path_s = rel.as_posix()
        except (ValueError, OSError):
            path_s = str(hit.path)
        return f"{path_s}:{hit.line}:{hit.column}  {hit.text}"

    def _open_item(self, item: QListWidgetItem | None) -> None:
        if item is None:
            return
        hit = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(hit, SearchHit):
            return
        self.hit_activated.emit(str(hit.path), hit.line, hit.column)
