"""Search algorithms for large buffers (Boyer-Moore planned)."""

from __future__ import annotations


def find_all(haystack: bytes, needle: bytes) -> list[int]:
    """Return start offsets of all non-overlapping matches (naive baseline)."""
    if not needle:
        return []
    offsets: list[int] = []
    start = 0
    while True:
        idx = haystack.find(needle, start)
        if idx < 0:
            break
        offsets.append(idx)
        start = idx + max(1, len(needle))
    return offsets
