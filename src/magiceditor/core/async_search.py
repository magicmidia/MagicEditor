"""Cancelable search over bytes (worker-friendly pure API)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from magiceditor.core.search import find_all


@dataclass
class SearchProgress:
    scanned: int
    total: int
    matches_so_far: int


CancelFn = Callable[[], bool]
ProgressFn = Callable[[SearchProgress], None]


def find_all_cancelable(
    haystack: bytes,
    needle: bytes,
    *,
    is_cancelled: CancelFn | None = None,
    on_progress: ProgressFn | None = None,
    chunk_size: int = 1_000_000,
    max_matches: int = 10_000,
) -> list[int] | None:
    """Boyer-Moore search in chunks; returns None if cancelled.

    For small buffers uses direct find_all. For large, scans windows with overlap.
    """
    if not needle:
        return []
    if is_cancelled and is_cancelled():
        return None
    n = len(haystack)
    if n <= chunk_size * 2:
        if on_progress:
            on_progress(SearchProgress(scanned=0, total=n, matches_so_far=0))
        hits = find_all(haystack, needle)
        if max_matches and len(hits) > max_matches:
            hits = hits[:max_matches]
        if on_progress:
            on_progress(SearchProgress(scanned=n, total=n, matches_so_far=len(hits)))
        return hits

    # Chunked scan with needle-length overlap
    overlap = max(0, len(needle) - 1)
    offsets: list[int] = []
    pos = 0
    while pos < n:
        if is_cancelled and is_cancelled():
            return None
        end = min(n, pos + chunk_size)
        window = haystack[pos:end]
        for rel in find_all(window, needle):
            abs_off = pos + rel
            if offsets and abs_off <= offsets[-1]:
                continue
            offsets.append(abs_off)
            if len(offsets) >= max_matches:
                if on_progress:
                    on_progress(SearchProgress(scanned=end, total=n, matches_so_far=len(offsets)))
                return offsets
        if on_progress:
            on_progress(SearchProgress(scanned=end, total=n, matches_so_far=len(offsets)))
        if end >= n:
            break
        pos = end - overlap
    return offsets
