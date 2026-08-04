"""Multi-cursor / occurrence helpers (pure)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CursorPos:
    line: int  # 0-based
    col: int  # 0-based char column


@dataclass(frozen=True, slots=True)
class SelectionSpan:
    """Single range selection in line/col."""

    start: CursorPos
    end: CursorPos

    def normalized(self) -> SelectionSpan:
        a, b = self.start, self.end
        if (a.line, a.col) <= (b.line, b.col):
            return self
        return SelectionSpan(start=b, end=a)


def find_next_occurrence(
    lines: list[str],
    needle: str,
    *,
    after_line: int,
    after_col: int,
    wrap: bool = True,
) -> CursorPos | None:
    """Find next occurrence of ``needle`` after (after_line, after_col)."""
    if not needle or not lines:
        return None
    start_line = max(0, after_line)
    # search from after_col on start_line
    for line_i in range(start_line, len(lines)):
        text = lines[line_i]
        start_col = after_col if line_i == start_line else 0
        idx = text.find(needle, start_col)
        if idx >= 0:
            return CursorPos(line=line_i, col=idx)
    if wrap:
        for line_i in range(0, start_line + 1):
            text = lines[line_i]
            idx = text.find(needle, 0)
            if idx >= 0 and (line_i < start_line or idx < after_col):
                return CursorPos(line=line_i, col=idx)
    return None


def find_all_occurrences(lines: list[str], needle: str, *, max_hits: int = 200) -> list[CursorPos]:
    """All occurrences of needle (capped)."""
    if not needle:
        return []
    hits: list[CursorPos] = []
    for li, text in enumerate(lines):
        start = 0
        while True:
            idx = text.find(needle, start)
            if idx < 0:
                break
            hits.append(CursorPos(line=li, col=idx))
            if len(hits) >= max_hits:
                return hits
            start = idx + max(1, len(needle))
    return hits


def restore_carets_after_multi_insert(
    carets: list[tuple[int, int]],
) -> tuple[tuple[int, int], list[tuple[int, int, int]]]:
    """Restore primary + extras after multi-cursor / column insert.

    ``carets`` are post-insert zero-width positions ``(line, col)``.
    Returns ``(primary, extras)`` where:
    - total carets (1 primary + len(extras)) == number of unique (line, col)
    - primary is the **bottommost** caret (last line, then rightmost col)
    - extras are the remaining carets as zero-width spans ``(line, col, col)``
    - no drops, no duplicates

    Invariant: N unique carets in -> N carets out (primary union extras).
    """
    if not carets:
        return (0, 0), []

    # Dedupe while preserving order of first appearance, then sort top→bottom
    seen: set[tuple[int, int]] = set()
    unique: list[tuple[int, int]] = []
    for pos in carets:
        key = (int(pos[0]), int(pos[1]))
        if key not in seen:
            seen.add(key)
            unique.append(key)
    unique.sort(key=lambda t: (t[0], t[1]))

    if len(unique) == 1:
        return unique[0], []

    # Primary = bottommost (last after top→bottom sort)
    primary = unique[-1]
    extras = [(ln, col, col) for ln, col in unique[:-1]]
    return primary, extras


def word_at(lines: list[str], line: int, col: int) -> tuple[str, int, int] | None:
    """Return (word, start_col, end_col) at position, or None."""
    if line < 0 or line >= len(lines):
        return None
    text = lines[line]
    if not text:
        return None
    col = max(0, min(col, len(text)))
    if col < len(text) and (text[col].isalnum() or text[col] == "_"):
        pass
    elif col > 0 and (text[col - 1].isalnum() or text[col - 1] == "_"):
        col -= 1
    else:
        return None
    start = col
    while start > 0 and (text[start - 1].isalnum() or text[start - 1] == "_"):
        start -= 1
    end = col
    while end < len(text) and (text[end].isalnum() or text[end] == "_"):
        end += 1
    if start == end:
        return None
    return text[start:end], start, end
