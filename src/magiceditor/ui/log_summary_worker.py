"""Background Log Summary worker (P6) — counts lines per severity level.

Reads lines through ``line_text(i)`` callables (piece table + line index,
mmap-backed for huge files) and never materializes the whole document.
Cancel is checked between chunks; progress emits ``(done, total)`` lines.
"""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from magiceditor.core.log_levels import LEVELS, count_levels
from magiceditor.ui.filter_lines_worker import CHUNK_LINES


class LogSummaryWorker(QThread):
    """QThread wrapper around ``core.log_levels.count_levels``."""

    progress = pyqtSignal(int, int)  # lines processed, total lines
    # None = cancelled; otherwise dict level -> count (all LEVELS keys).
    finished_counts = pyqtSignal(object)

    def __init__(
        self,
        *,
        line_count: int,
        line_text: Callable[[int], str],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._line_count = line_count
        self._line_text = line_text
        self._cancelled = False

    def request_cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        counts = dict.fromkeys(LEVELS, 0)
        total = self._line_count
        start = 0
        while start < total:
            if self._cancelled:
                self.finished_counts.emit(None)
                return
            end = min(start + CHUNK_LINES, total)
            chunk = (self._line_text(i) for i in range(start, end))
            chunk_counts = count_levels(chunk)
            for level in LEVELS:
                counts[level] += chunk_counts[level]
            start = end
            self.progress.emit(start, total)
        self.finished_counts.emit(None if self._cancelled else counts)
