"""Log severity levels (P6 — Log Lens) — pure core, no Qt.

Levels (highest first): ``error``, ``warn``, ``info``, ``debug``. Matching is
case-insensitive with word boundaries, so ``information`` does not count as
INFO. A line counts for the highest level that matches it. The same regexes
feed both the syntax rules (``core.syntax.rules``) and the summary counts.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable

LEVELS: tuple[str, ...] = ("error", "warn", "info", "debug")

# Ordered highest → lowest severity. First match wins for a line.
LEVEL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("error", re.compile(r"\b(?:FATAL|CRITICAL|ERROR|Exception|Traceback)\b", re.I)),
    ("warn", re.compile(r"\bWARN(?:ING)?\b", re.I)),
    ("info", re.compile(r"\bINFO\b", re.I)),
    ("debug", re.compile(r"\b(?:DEBUG|TRACE)\b", re.I)),
)


def line_level(text: str) -> str | None:
    """Highest severity level found in ``text``, or ``None``."""
    for level, pattern in LEVEL_PATTERNS:
        if pattern.search(text):
            return level
    return None


def count_levels(lines: Iterable[str]) -> dict[str, int]:
    """Streaming count per level over any iterable of lines (all 4 keys)."""
    counts = dict.fromkeys(LEVELS, 0)
    for text in lines:
        level = line_level(text)
        if level is not None:
            counts[level] += 1
    return counts


def next_line_with_level(
    line_count: int,
    line_text: Callable[[int], str],
    level: str,
    start_line: int,
) -> int | None:
    """0-based index of the next line at ``level`` after ``start_line``.

    ``start_line`` is 0-based and exclusive (pass -1 to start from the top).
    Wraps around once. Returns ``None`` for an unknown level or no match.
    Iterates via ``line_text(i)`` — never materializes the document.
    """
    if level not in LEVELS or line_count <= 0:
        return None
    for offset in range(1, line_count + 1):
        index = (start_line + offset) % line_count
        if line_level(line_text(index)) == level:
            return index
    return None
