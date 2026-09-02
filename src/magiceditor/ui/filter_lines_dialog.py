"""Filter Lines dialog (P1) — extract matching lines into a new tab.

Runs a FilterLinesWorker over the source document's lines (chunked,
cancellable, with progress) and emits ``result_ready`` so the caller can
open the extracted lines in a new tab. Modal: the source document cannot
be edited while the filter runs, so worker reads stay consistent.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, ClassVar

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from magiceditor.core.line_filter import DEFAULT_MAX_MATCHES, make_matcher
from magiceditor.core.text_match import PatternError
from magiceditor.ui.filter_lines_worker import FilterLinesWorker

HISTORY_LIMIT = 10


class FilterLinesDialog(QDialog):
    """Modal pattern/options dialog with progress and real cancel."""

    # pattern, extracted text, match count, truncated
    result_ready = pyqtSignal(str, str, int, bool)

    _history: ClassVar[list[str]] = []

    def __init__(
        self,
        *,
        line_count: int,
        line_text: Callable[[int], str],
        max_matches: int = DEFAULT_MAX_MATCHES,
        tr: Any | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._line_count = line_count
        self._line_text = line_text
        self._max_matches = max_matches
        self._tr = tr
        self._worker: FilterLinesWorker | None = None
        self.setModal(True)
        self.setMinimumWidth(460)
        self.setObjectName("filterLinesDialog")
        self.setWindowTitle(self._t("filter.title", "Filtrar linhas"))

        self.pattern_combo = QComboBox(self)
        self.pattern_combo.setEditable(True)
        self.pattern_combo.addItems(self._history)
        self.pattern_combo.setCurrentText("")
        if self.pattern_combo.lineEdit() is not None:
            self.pattern_combo.lineEdit().setPlaceholderText(
                self._t("filter.placeholder", "Texto ou regex…")
            )

        self.case_box = QCheckBox(self._t("find.match_case", "Diferenciar maiúsculas"), self)
        self.regex_box = QCheckBox(self._t("find.regex", "Expressão regular"), self)
        self.invert_box = QCheckBox(
            self._t("filter.invert", "Inverter (linhas que NÃO casam)"), self
        )

        self._info = QLabel(
            self._t("filter.total_lines", "Linhas no documento: {n}").format(n=line_count),
            self,
        )
        self._status = QLabel("", self)
        self._status.setObjectName("filterLinesStatus")
        self._progress = QProgressBar(self)
        self._progress.setRange(0, max(1, line_count))
        self._progress.setValue(0)
        self._progress.hide()

        self._btn_filter = QPushButton(self._t("filter.run", "Filtrar"), self)
        self._btn_filter.setDefault(True)
        self._btn_filter.clicked.connect(self.start_filter)
        self._btn_cancel = QPushButton(self._t("dialog.cancel", "Cancelar"), self)
        self._btn_cancel.clicked.connect(self._on_cancel)

        options = QHBoxLayout()
        options.setSpacing(12)
        options.addWidget(self.case_box)
        options.addWidget(self.regex_box)
        options.addWidget(self.invert_box)
        options.addStretch(1)

        buttons = QHBoxLayout()
        buttons.setSpacing(6)
        buttons.addStretch(1)
        buttons.addWidget(self._btn_filter)
        buttons.addWidget(self._btn_cancel)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)
        root.addWidget(self.pattern_combo)
        root.addLayout(options)
        root.addWidget(self._info)
        root.addWidget(self._progress)
        root.addWidget(self._status)
        root.addLayout(buttons)

        if self.pattern_combo.lineEdit() is not None:
            self.pattern_combo.lineEdit().returnPressed.connect(self.start_filter)
        QShortcut(QKeySequence("Esc"), self, activated=self._on_cancel)
        self.pattern_combo.setFocus()

    def _t(self, key: str, default: str) -> str:
        if self._tr is not None:
            return self._tr.t(key, default)
        return default

    def start_filter(self) -> None:
        """Validate the pattern and launch the worker (also used by tests)."""
        pattern = self.pattern_combo.currentText()
        if not pattern:
            self._status.setText(self._t("find.enter_text", "Digite o texto a localizar."))
            return
        try:
            matcher = make_matcher(
                pattern,
                case_sensitive=self.case_box.isChecked(),
                use_regex=self.regex_box.isChecked(),
                invert=self.invert_box.isChecked(),
            )
        except PatternError as exc:
            self._status.setText(
                self._t("find.invalid_regex", "Regex inválida: {err}").format(err=exc)
            )
            return
        if self._worker is not None and self._worker.isRunning():
            return
        self._push_history(pattern)
        self._btn_filter.setEnabled(False)
        self._progress.setValue(0)
        self._progress.show()
        self._status.setText("")
        worker = FilterLinesWorker(
            line_count=self._line_count,
            line_text=self._line_text,
            matcher=matcher,
            max_matches=self._max_matches,
            parent=self,
        )
        worker.progress.connect(self._on_progress)
        worker.finished_matches.connect(self._on_finished)
        self._worker = worker
        worker.start()

    def _push_history(self, pattern: str) -> None:
        history = self._history
        if pattern in history:
            history.remove(pattern)
        history.insert(0, pattern)
        del history[HISTORY_LIMIT:]
        # Refresh the combo without losing the current text.
        current = self.pattern_combo.currentText()
        self.pattern_combo.clear()
        self.pattern_combo.addItems(history)
        self.pattern_combo.setCurrentText(current)

    def _on_progress(self, done: int, total: int) -> None:
        self._progress.setRange(0, max(1, total))
        self._progress.setValue(done)
        self._status.setText(
            self._t("filter.running", "Filtrando… {done}/{total} linhas").format(
                done=done, total=total
            )
        )

    def _on_finished(self, result: object) -> None:
        worker = self._worker
        self._worker = None
        self._btn_filter.setEnabled(True)
        self._progress.hide()
        if result is None:
            self._status.setText(self._t("filter.cancelled", "Filtro cancelado."))
            return
        lines, truncated = result
        if not lines:
            self._status.setText(self._t("find.none", "Nenhuma ocorrência."))
            return
        text = "\n".join(lines)
        if truncated:
            text += "\n" + self._t(
                "filter.truncated_note", "… [resultado truncado em {max} linhas]"
            ).format(max=self._max_matches)
        pattern = self.pattern_combo.currentText()
        if worker is not None:
            worker.wait(200)
        self.result_ready.emit(pattern, text, len(lines), truncated)
        self.accept()

    def _on_cancel(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.request_cancel()
            self._status.setText(self._t("find_files.cancelling", "Cancelando…"))
            return
        self.reject()

    def reject(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.request_cancel()
        super().reject()

    def keyPressEvent(self, event: Any) -> None:
        # Keep Enter on the combo from double-triggering the default button.
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.pattern_combo.hasFocus():
            self.start_filter()
            return
        super().keyPressEvent(event)
