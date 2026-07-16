"""Quick Open — filter files in workspace (Ctrl+P mockup search)."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
}
_MAX_FILES = 800


class QuickOpenDialog(QDialog):
    """Fuzzy-ish filename search under a workspace root."""

    path_chosen = pyqtSignal(str)

    def __init__(
        self,
        root: Path | str | None,
        parent: QWidget | None = None,
        *,
        open_paths: list[str] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Quick Open")
        self.setMinimumSize(480, 360)
        self.setObjectName("quickOpenDialog")

        self._root = Path(root) if root else None
        self._all: list[tuple[str, str]] = []  # (display, path)

        self._input = QLineEdit(self)
        self._input.setPlaceholderText("Search files…")
        self._input.setObjectName("quickOpenInput")
        self._list = QListWidget(self)
        self._list.setObjectName("quickOpenList")
        self._status = QLabel("", self)
        self._status.setObjectName("findDialogStatus")

        row = QHBoxLayout()
        row.addWidget(self._input, 1)

        root_l = QVBoxLayout(self)
        root_l.setContentsMargins(12, 12, 12, 12)
        root_l.setSpacing(8)
        root_l.addLayout(row)
        root_l.addWidget(self._list, 1)
        root_l.addWidget(self._status)

        self._input.textChanged.connect(self._filter)
        self._input.returnPressed.connect(self._accept_current)
        self._list.itemActivated.connect(self._activate_item)
        self._list.itemDoubleClicked.connect(self._activate_item)
        QShortcut(QKeySequence("Esc"), self, activated=self.reject)
        QShortcut(QKeySequence("Down"), self, activated=self._focus_list)
        QShortcut(QKeySequence("Up"), self, activated=self._focus_list)

        self._build_index(open_paths or [])
        self._filter("")
        self._input.setFocus()

    def _build_index(self, open_paths: list[str]) -> None:
        seen: set[str] = set()
        # Prefer currently open paths first
        for p in open_paths:
            path = Path(p)
            if path.is_file():
                key = str(path.resolve())
                if key not in seen:
                    seen.add(key)
                    self._all.append((path.name + "  —  " + key, key))

        if self._root is None or not self._root.is_dir():
            return
        root = self._root
        count = 0
        for dirpath, dirnames, filenames in __import__("os").walk(root):
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
            base = Path(dirpath)
            for name in filenames:
                if count >= _MAX_FILES:
                    return
                p = base / name
                try:
                    key = str(p.resolve())
                except OSError:
                    continue
                if key in seen:
                    continue
                seen.add(key)
                try:
                    rel = p.relative_to(root).as_posix()
                except ValueError:
                    rel = p.name
                self._all.append((rel, key))
                count += 1

    def _filter(self, text: str) -> None:
        self._list.clear()
        q = text.strip().lower()
        hits = 0
        for display, path in self._all:
            if q and q not in display.lower() and q not in Path(path).name.lower():
                continue
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, path)
            self._list.addItem(item)
            hits += 1
            if hits >= 80:
                break
        self._status.setText(f"{hits} file(s)" + (" (capped)" if hits >= 80 else ""))
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _focus_list(self) -> None:
        self._list.setFocus()

    def _accept_current(self) -> None:
        item = self._list.currentItem()
        if item is None and self._list.count() > 0:
            item = self._list.item(0)
        self._activate_item(item)

    def _activate_item(self, item: QListWidgetItem | None) -> None:
        if item is None:
            return
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.path_chosen.emit(str(path))
            self.accept()
