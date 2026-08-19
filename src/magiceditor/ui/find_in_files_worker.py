"""Background Find-in-Files worker (K5)."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from magiceditor.services.folder_search import search_folder


class FolderSearchWorker(QThread):
    finished_hits = pyqtSignal(object)

    def __init__(
        self,
        root: Path,
        needle: str,
        *,
        case_sensitive: bool,
        use_regex: bool,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._root = root
        self._needle = needle
        self._case = case_sensitive
        self._regex = use_regex
        self._cancel = False

    def request_cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        hits = search_folder(
            self._root,
            self._needle,
            case_sensitive=self._case,
            use_regex=self._regex,
            is_cancelled=lambda: self._cancel,
        )
        self.finished_hits.emit(hits if hits is not None else None)
