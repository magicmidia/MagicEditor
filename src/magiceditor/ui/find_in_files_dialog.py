"""Find in Files / open tabs — workspace or editor buffers."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
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

from magiceditor.core.text_match import PatternError, compile_pattern
from magiceditor.services.folder_search import SearchHit, search_folder, search_texts


class FindInFilesDialog(QDialog):
    """Modal multi-file search.

    Emits ``hit_activated(path, line, column, source_key)`` —
    ``source_key`` is empty for workspace files, or ``tab:N`` for open tabs.
    """

    hit_activated = pyqtSignal(str, int, int, str)

    def __init__(
        self,
        root: Path | str | None,
        parent: QWidget | None = None,
        *,
        open_sources: list[tuple[str, str, str]] | None = None,
    ) -> None:
        super().__init__(parent)
        self._root = Path(root) if root else None
        self._open_sources = open_sources or []
        self.setModal(True)
        self.setWindowTitle("Find in Files")
        self.setMinimumSize(580, 440)
        self.setObjectName("findInFilesDialog")

        self.find_input = QLineEdit(self)
        self.find_input.setPlaceholderText("Search…")
        self.case_box = QCheckBox("Match case", self)
        self.regex_box = QCheckBox("Regex", self)
        self.scope_box = QComboBox(self)
        self.scope_box.addItem("Workspace folder", "workspace")
        self.scope_box.addItem("Open tabs", "tabs")
        if self._root is None or not self._root.is_dir():
            # Prefer open tabs when no workspace
            idx = self.scope_box.findData("tabs")
            if idx >= 0:
                self.scope_box.setCurrentIndex(idx)

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
        row.addWidget(self.scope_box)
        row.addWidget(self.case_box)
        row.addWidget(self.regex_box)
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
        self._update_status_idle()
        self.find_input.setFocus()

    def _update_status_idle(self) -> None:
        scope = self.scope_box.currentData()
        if scope == "tabs":
            n = len(self._open_sources)
            self._status.setText(f"Open tabs: {n} buffer(s).")
        elif self._root and self._root.is_dir():
            self._status.setText(f"Workspace: {self._root}")
        else:
            self._status.setText("No workspace folder — choose Open tabs or Open Folder first.")

    def run_search(self) -> None:
        needle = self.find_input.text()
        if not needle:
            self._status.setText("Enter text to find.")
            return
        if self.regex_box.isChecked():
            try:
                compile_pattern(
                    needle,
                    case_sensitive=self.case_box.isChecked(),
                    use_regex=True,
                )
            except PatternError as exc:
                self._status.setText(f"Invalid regex: {exc}")
                return

        self._results.clear()
        self._status.setText("Searching…")
        scope = self.scope_box.currentData()
        case = self.case_box.isChecked()
        use_re = self.regex_box.isChecked()

        if scope == "tabs":
            if not self._open_sources:
                self._status.setText("No open tabs to search.")
                return
            hits = search_texts(
                self._open_sources,
                needle,
                case_sensitive=case,
                use_regex=use_re,
            )
        else:
            if self._root is None or not self._root.is_dir():
                self._status.setText("Open a folder (File → Open Folder) to search.")
                return
            hits = search_folder(
                self._root,
                needle,
                case_sensitive=case,
                use_regex=use_re,
            )

        if not hits:
            self._status.setText("No matches.")
            return

        root_resolved: Path | None = None
        if self._root and self._root.is_dir():
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

    def _format_hit(self, hit: SearchHit, root: Path | None) -> str:
        if hit.label:
            path_s = hit.label
        elif root is not None:
            try:
                path_s = hit.path.resolve().relative_to(root).as_posix()
            except (ValueError, OSError):
                path_s = str(hit.path)
        else:
            path_s = str(hit.path)
        return f"{path_s}:{hit.line}:{hit.column}  {hit.text}"

    def _open_item(self, item: QListWidgetItem | None) -> None:
        if item is None:
            return
        hit = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(hit, SearchHit):
            return
        key = hit.source_key or ""
        self.hit_activated.emit(str(hit.path), hit.line, hit.column, key)
