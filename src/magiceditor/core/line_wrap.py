"""Soft-wrap ranges for a single display line (Qt-free)."""

from __future__ import annotations

from collections.abc import Callable


def wrap_ranges(
    text: str,
    max_width: int,
    width_of_or_char_width: Callable[[str], int] | int,
) -> list[tuple[int, int]]:
    """Return ``(start, end)`` index pairs into ``text`` for each visual row.

    Prefer breaking at spaces when the line exceeds ``max_width``.
    If an int ``char_width`` is provided (monospace font), wrapping is strictly O(N)
    without repetitive font metric shaping calls.
    """
    n = len(text)
    if n == 0:
        return [(0, 0)]
    if max_width <= 0:
        return [(0, n)]

    if isinstance(width_of_or_char_width, int):
        char_width = max(1, width_of_or_char_width)
        chars_per_row = max(1, max_width // char_width)
        if n <= chars_per_row:
            return [(0, n)]

        ranges: list[tuple[int, int]] = []
        i = 0
        while i < n:
            if i + chars_per_row >= n:
                ranges.append((i, n))
                break
            limit = i + chars_per_row
            chunk = text[i:limit]
            sp = chunk.rfind(" ")
            if sp > 0:
                best = i + sp + 1
            else:
                best = limit
            ranges.append((i, best))
            i = best
        return ranges or [(0, n)]

    width_of = width_of_or_char_width
    if width_of(text) <= max_width:
        return [(0, n)]

    ranges_cb: list[tuple[int, int]] = []
    i = 0
    while i < n:
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
            ranges_cb.append((i, n))
            break
        chunk = text[i:best]
        sp = chunk.rfind(" ")
        if sp > 0:
            best = i + sp + 1
        if best <= i:
            best = i + 1
        ranges_cb.append((i, best))
        i = best
    return ranges_cb or [(0, n)]


def expand_tabs(text: str, tab_size: int = 4) -> str:
    return text.replace("\t", " " * tab_size)
