"""Background Filter Lines worker (P1) — iterates the document in chunks.

Reads lines through ``line_text(i)`` callables (piece table + line index,
mmap-backed for huge files) and never materializes the whole document.
Cancel is checked between chunks; progress emits ``(done, total)`` lines.
"""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from magiceditor.core.line_filter import DEFAULT_MAX_MATCHES, filter_lines

CHUNK_LINES = 10_000


class FilterLinesWorker(QThread):
    """QThread wrapper around ``core.line_filter.filter_lines``."""

    progress = pyqtSignal(int, int)  # lines processed, total lines
    # None = cancelled; otherwise (lines "N: text", truncated).
    finished_matches = pyqtSignal(object)

    def __init__(
        self,
        *,
        line_count: int,
        line_text: Callable[[int], str],
        matcher: Callable[[str], bool],
        max_matches: int = DEFAULT_MAX_MATCHES,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._line_count = line_count
        self._line_text = line_text
        self._matcher = matcher
        self._max = max_matches
        self._cancelled = False

    def request_cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        out: list[str] = []
        truncated = False
        total = self._line_count
        start = 0
        while start < total:
            if self._cancelled:
                self.finished_matches.emit(None)
                return
            end = min(start + CHUNK_LINES, total)
            chunk = (self._line_text(i) for i in range(start, end))
            # Ask for one match beyond the remaining capacity: if it shows
            # up, the result is genuinely truncated.
            capacity = self._max - len(out) + 1
            for num, text in filter_lines(chunk, self._matcher, max_matches=capacity):
                out.append(f"{start + num}: {text}")
            if len(out) > self._max:
                out.pop()
                truncated = True
            start = end
            self.progress.emit(start, total)
            if truncated:
                break
        self.finished_matches.emit(None if self._cancelled else (out, truncated))
