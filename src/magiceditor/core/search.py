"""Search algorithms for large buffers (Boyer-Moore)."""

from __future__ import annotations


def _build_bad_char_table(needle: bytes) -> dict[int, int]:
    """Last-occurrence shift table for Boyer-Moore bad-character rule."""
    table: dict[int, int] = {}
    last = len(needle) - 1
    for i, byte in enumerate(needle[:-1]):
        table[byte] = last - i
    return table


def find_all(haystack: bytes, needle: bytes) -> list[int]:
    """Return start offsets of all non-overlapping matches (Boyer-Moore)."""
    if not needle:
        return []
    n = len(needle)
    m = len(haystack)
    if n > m:
        return []

    # Fast path for tiny needles
    if n == 1:
        target = needle[0]
        return [i for i, b in enumerate(haystack) if b == target]

    bad = _build_bad_char_table(needle)
    offsets: list[int] = []
    i = 0
    while i <= m - n:
        j = n - 1
        while j >= 0 and haystack[i + j] == needle[j]:
            j -= 1
        if j < 0:
            offsets.append(i)
            i += n
        else:
            shift = bad.get(haystack[i + j], n)
            i += max(1, shift)
    return offsets
