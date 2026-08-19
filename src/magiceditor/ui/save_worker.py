"""Background save (K15) — temp+replace runs off the UI thread."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from magiceditor.core.document import Document
from magiceditor.services.document_io import save_document


class SaveWorker(QThread):
    succeeded = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(
        self,
        document: Document,
        path: Path | str | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._document = document
        self._path = path

    def run(self) -> None:
        try:
            saved = save_document(self._document, self._path)
            target = saved.path
            self.succeeded.emit(str(target) if target is not None else "")
        except OSError as exc:
            self.failed.emit(str(exc))


def begin_document_save(
    parent: QObject, document: Document, path: Path | str | None, on_ok, on_err
) -> SaveWorker:
    """Start a SaveWorker (K15). UI thread only connects signals and starts."""
    worker = SaveWorker(document, path, parent)
    worker.succeeded.connect(on_ok)
    worker.failed.connect(on_err)
    worker.start()
    return worker
