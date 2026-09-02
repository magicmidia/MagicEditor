"""Streaming text statistics (chars, words, lines) over text chunks.

Consumes an iterable of ``str`` chunks so stats can be computed over huge
documents without materializing the full text. Word and line boundaries
split between chunks are handled via per-accumulator edge state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


@dataclass(frozen=True)
class TextStats:
    """Accumulated statistics for a text document (or selection).

    - ``chars``: total characters, including whitespace and line breaks.
    - ``chars_no_spaces``: characters excluding all whitespace
      (spaces, tabs, CR, LF, unicode spaces).
    - ``words``: whitespace-delimited word count (``str.split`` semantics).
    - ``lines``: line count; a final line without a trailing break still
      counts. ``\\r\\n``, ``\\r`` and ``\\n`` each count as one break.
    - ``non_empty_lines``: lines containing at least one non-whitespace char.
    """

    chars: int = 0
    chars_no_spaces: int = 0
    words: int = 0
    lines: int = 0
    non_empty_lines: int = 0


class _StatsAccumulator:
    """Stateful accumulator; safe across arbitrary chunk boundaries."""

    def __init__(self) -> None:
        self.chars = 0
        self.chars_no_spaces = 0
        self.words = 0
        self.lines = 0
        self.non_empty_lines = 0
        self._in_word = False
        self._prev_cr = False
        self._line_has_content = False
        self._line_chars = 0

    def _close_line(self) -> None:
        self.lines += 1
        if self._line_has_content:
            self.non_empty_lines += 1
        self._line_has_content = False
        self._line_chars = 0

    def feed(self, chunk: str) -> None:
        for ch in chunk:
            self.chars += 1
            if ch.isspace():
                self._in_word = False
            else:
                self.chars_no_spaces += 1
                if not self._in_word:
                    self.words += 1
                    self._in_word = True
                self._line_has_content = True

            if ch == "\r":
                self._close_line()
                self._prev_cr = True
            elif ch == "\n":
                if self._prev_cr:
                    # LF finishing a CRLF split (possibly across chunks).
                    self._prev_cr = False
                else:
                    self._close_line()
            else:
                self._prev_cr = False
                self._line_chars += 1

    def finish(self) -> TextStats:
        # A final line without a trailing break still counts as a line.
        if self._line_chars > 0:
            self._close_line()
        return TextStats(
            chars=self.chars,
            chars_no_spaces=self.chars_no_spaces,
            words=self.words,
            lines=self.lines,
            non_empty_lines=self.non_empty_lines,
        )


def compute_stats(chunks: Iterable[str]) -> TextStats:
    """Accumulate :class:`TextStats` over an iterable of text chunks.

    Streaming: chunks are consumed one at a time and edge state (word in
    progress, pending ``\\r`` of a split CRLF, current-line content) is kept
    between them, so the result equals stats for the concatenated text.
    """
    acc = _StatsAccumulator()
    for chunk in chunks:
        acc.feed(chunk)
    return acc.finish()


def stats_for_text(text: str) -> TextStats:
    """Convenience wrapper: stats for a single in-memory string."""
    return compute_stats((text,))
