"""Soft-wrap ranges for a single display line (Qt-free)."""

from __future__ import annotations

from collections.abc import Callable


def wrap_ranges(
    text: str,
    max_width: int,
    width_of: Callable[[str], int],
) -> list[tuple[int, int]]:
    """Return ``(start, end)`` index pairs into ``text`` for each visual row.

    Prefer breaking at spaces when the line exceeds ``max_width``.
    ``width_of`` measures a substring (e.g. fontMetrics.horizontalAdvance).
    """
    n = len(text)
    if n == 0:
        return [(0, 0)]
    if max_width <= 0:
        return [(0, n)]
    if width_of(text) <= max_width:
        return [(0, n)]

    ranges: list[tuple[int, int]] = []
    i = 0
    while i < n:
        # Binary search max end exclusive with width <= max_width
        lo, hi = i + 1, n
        best = i + 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if width_of(text[i:mid]) <= max_width:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1
        if best >= n:
            ranges.append((i, n))
            break
        # Prefer last space in (i, best]
        chunk = text[i:best]
        sp = chunk.rfind(" ")
        if sp > 0:
            best = i + sp + 1
        if best <= i:
            best = i + 1
        ranges.append((i, best))
        i = best
    return ranges or [(0, n)]


def expand_tabs(text: str, tab_size: int = 4) -> str:
    return text.replace("\t", " " * tab_size)
