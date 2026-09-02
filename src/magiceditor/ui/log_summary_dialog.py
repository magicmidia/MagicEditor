"""Log Summary dialog (P6) — severity counts + "go to next" navigation.

Starts a LogSummaryWorker over the source document's lines (chunked,
cancellable, with progress) as soon as it is shown. Each level row has a
counter and a "go to next" button that emits ``goto_level_requested``; the
caller owns cursor navigation. Modal: the source document cannot be edited
while the count runs, so worker reads stay consistent.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from magiceditor.core.log_levels import LEVELS
from magiceditor.ui.log_summary_worker import LogSummaryWorker

_LEVEL_LABELS: dict[str, str] = {
    "error": "ERROR / FATAL",
    "warn": "WARN",
    "info": "INFO",
    "debug": "DEBUG / TRACE",
}


class LogSummaryDialog(QDialog):
    """Modal severity summary with per-level navigation buttons."""

    # severity level whose "go to next" button was clicked
    goto_level_requested = pyqtSignal(str)

    def __init__(
        self,
        *,
        line_count: int,
        line_text: Callable[[int], str],
        tr: Any | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._line_count = line_count
        self._line_text = line_text
        self._tr = tr
        self._worker: LogSummaryWorker | None = None
        self.counts: dict[str, int] = dict.fromkeys(LEVELS, 0)
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setObjectName("logSummaryDialog")
        self.setWindowTitle(self._t("log_summary.title", "Resumo do log"))

        self._info = QLabel(
            self._t("filter.total_lines", "Linhas no documento: {n}").format(n=line_count),
            self,
        )
        self._status = QLabel("", self)
        self._status.setObjectName("logSummaryStatus")
        self._progress = QProgressBar(self)
        self._progress.setRange(0, max(1, line_count))
        self._progress.setValue(0)

        self._count_labels: dict[str, QLabel] = {}
        self._next_buttons: dict[str, QPushButton] = {}
        rows = QVBoxLayout()
        rows.setSpacing(6)
        for level in LEVELS:
            row = QHBoxLayout()
            row.setSpacing(8)
            name = QLabel(_LEVEL_LABELS[level], self)
            name.setMinimumWidth(110)
            count = QLabel("—", self)
            count.setObjectName(f"logSummaryCount_{level}")
            count.setMinimumWidth(60)
            button = QPushButton(self._t("log_summary.next", "Ir ao próximo"), self)
            button.setObjectName(f"logSummaryNext_{level}")
            button.setEnabled(False)
            button.clicked.connect(lambda _checked=False, lv=level: self._on_next(lv))
            row.addWidget(name)
            row.addWidget(count)
            row.addStretch(1)
            row.addWidget(button)
            rows.addLayout(row)
            self._count_labels[level] = count
            self._next_buttons[level] = button

        self._btn_close = QPushButton(self._t("dialog.close", "Fechar"), self)
        self._btn_close.clicked.connect(self._on_close)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(self._btn_close)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)
        root.addWidget(self._info)
        root.addWidget(self._progress)
        root.addWidget(self._status)
        root.addLayout(rows)
        root.addLayout(buttons)

        # Start counting after the dialog is visible.
        QTimer.singleShot(0, self.start_count)

    def _t(self, key: str, default: str) -> str:
        if self._tr is not None:
            return self._tr.t(key, default)
        return default

    def start_count(self) -> None:
        """Launch the counting worker (also used by tests)."""
        if self._worker is not None and self._worker.isRunning():
            return
        for button in self._next_buttons.values():
            button.setEnabled(False)
        self._progress.setValue(0)
        worker = LogSummaryWorker(
            line_count=self._line_count,
            line_text=self._line_text,
            parent=self,
        )
        worker.progress.connect(self._on_progress)
        worker.finished_counts.connect(self._on_finished)
        self._worker = worker
        worker.start()

    def _on_next(self, level: str) -> None:
        self.goto_level_requested.emit(level)

    def _on_progress(self, done: int, total: int) -> None:
        self._progress.setRange(0, max(1, total))
        self._progress.setValue(done)
        self._status.setText(
            self._t("log_summary.running", "Contando… {done}/{total} linhas").format(
                done=done, total=total
            )
        )

    def _on_finished(self, result: object) -> None:
        worker = self._worker
        self._worker = None
        self._progress.setValue(self._progress.maximum())
        if result is None:
            self._status.setText(self._t("log_summary.cancelled", "Contagem cancelada."))
            return
        self.counts = dict(result)
        self._status.setText("")
        for level in LEVELS:
            n = self.counts[level]
            self._count_labels[level].setText(str(n))
            self._next_buttons[level].setEnabled(n > 0)
        if worker is not None:
            worker.wait(200)

    def _on_close(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.request_cancel()
            self._status.setText(self._t("find_files.cancelling", "Cancelando…"))
            return
        self.reject()

    def reject(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.request_cancel()
        super().reject()
