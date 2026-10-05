"""Checksum dialog (Tools menu) — hashes the on-disk file in a worker thread.

Uses ``core.checksum.file_hashes`` (streaming, 1 MiB chunks). Progress is
indeterminate because the core API is monolithic; Cancel discards the result
(the worker may finish reading in the background and is then dropped).
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from magiceditor.core.checksum import DEFAULT_ALGORITHMS, file_hashes

ALGO_LABELS = {
    "md5": "MD5",
    "sha1": "SHA-1",
    "sha256": "SHA-256",
    "sha384": "SHA-384",
    "sha512": "SHA-512",
    "blake2b": "BLAKE2b",
}


class ChecksumWorker(QThread):
    """QThread wrapper around ``file_hashes`` (pattern of SaveWorker)."""

    finished_hashes = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(
        self,
        path: Path | str,
        parent: QObject | None = None,
        *,
        algorithms: tuple[str, ...] | None = None,
    ) -> None:
        super().__init__(parent)
        self._path = path
        self._algorithms = tuple(algorithms) if algorithms else DEFAULT_ALGORITHMS
        self._cancelled = False

    def request_cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            result = file_hashes(self._path, algorithms=self._algorithms)
        except (OSError, ValueError) as exc:
            if not self._cancelled:
                self.failed.emit(str(exc))
            return
        if not self._cancelled:
            self.finished_hashes.emit(result)


def _format_size(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB ({size} B)"
    if size >= 1024:
        return f"{size / 1024:.1f} KB ({size} B)"
    return f"{size} B"


class ChecksumDialog(QDialog):
    """Shows MD5/SHA-1/SHA-256 of the file on disk, with copy buttons."""

    def __init__(
        self,
        path: Path | str,
        *,
        dirty: bool = False,
        tr: QObject | None = None,
        parent: QWidget | None = None,
        algorithms: tuple[str, ...] | None = None,
    ) -> None:
        super().__init__(parent)
        self._tr = tr
        self._algorithms = tuple(algorithms) if algorithms else DEFAULT_ALGORITHMS
        self._worker: ChecksumWorker | None = None
        self.setWindowTitle(self._t("checksum.title", "Checksum do arquivo"))
        self.setModal(True)
        self.resize(560, 0)

        layout = QVBoxLayout(self)
        path_label = QLabel(self._t("checksum.path", "Arquivo: {path}").format(path=str(path)))
        path_label.setWordWrap(True)
        layout.addWidget(path_label)
        try:
            size = Path(path).stat().st_size
        except OSError:
            size = -1
        if size >= 0:
            layout.addWidget(
                QLabel(self._t("checksum.size", "Tamanho: {size}").format(size=_format_size(size)))
            )
        if dirty:
            warn = QLabel(
                self._t(
                    "checksum.dirty_warning",
                    "O buffer tem alterações não salvas — o hash é do arquivo em disco.",
                )
            )
            warn.setObjectName("checksumDirtyWarning")
            warn.setWordWrap(True)
            layout.addWidget(warn)

        self._progress = QProgressBar(self)
        self._progress.setRange(0, 0)  # indeterminate
        layout.addWidget(self._progress)

        form = QFormLayout()
        self._fields: dict[str, QLineEdit] = {}
        for algo in self._algorithms:
            row = QWidget(self)
            row_lay = QHBoxLayout(row)
            row_lay.setContentsMargins(0, 0, 0, 0)
            field = QLineEdit(self)
            field.setReadOnly(True)
            field.setPlaceholderText("…")
            copy_btn = QPushButton(self._t("checksum.copy", "Copiar"), self)
            copy_btn.setEnabled(False)
            copy_btn.clicked.connect(
                lambda checked=False, f=field, b=copy_btn: self._copy_field(f, b)
            )
            row_lay.addWidget(field, 1)
            row_lay.addWidget(copy_btn, 0)
            form.addRow(ALGO_LABELS.get(algo, algo), row)
            self._fields[algo] = field
            field.setProperty("_copy_btn", copy_btn)
        layout.addLayout(form)

        self._error = QLabel("")
        self._error.setObjectName("checksumError")
        self._error.setWordWrap(True)
        self._error.hide()
        layout.addWidget(self._error)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.rejected.connect(self.reject)
        self._cancel_btn = QPushButton(self._t("dialog.cancel", "Cancelar"), self)
        self._cancel_btn.clicked.connect(self.reject)
        buttons.addButton(self._cancel_btn, QDialogButtonBox.ButtonRole.RejectRole)
        layout.addWidget(buttons)

        self._start_worker(path, self._algorithms)

    def _t(self, key: str, default: str) -> str:
        tr = self._tr
        if tr is not None and hasattr(tr, "t"):
            return tr.t(key, default)  # type: ignore[no-any-return,union-attr]
        return default

    def _start_worker(self, path: Path | str, algorithms: tuple[str, ...]) -> None:
        worker = ChecksumWorker(path, self, algorithms=algorithms)
        worker.finished_hashes.connect(self._on_finished)
        worker.failed.connect(self._on_failed)
        worker.start()
        self._worker = worker

    def _on_finished(self, hashes: dict) -> None:
        self._progress.hide()
        self._cancel_btn.setEnabled(False)
        for algo, field in self._fields.items():
            field.setText(str(hashes.get(algo, "")))
            btn = field.property("_copy_btn")
            if isinstance(btn, QPushButton):
                btn.setEnabled(True)

    def _on_failed(self, message: str) -> None:
        self._progress.hide()
        self._cancel_btn.setEnabled(False)
        self._error.setText(self._t("checksum.error", "Erro: {err}").format(err=message))
        self._error.show()

    def _copy_field(self, field: QLineEdit, button: QPushButton) -> None:
        clipboard = QApplication.clipboard()
        if clipboard is not None and field.text():
            clipboard.setText(field.text())

    def reject(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.request_cancel()
        super().reject()
