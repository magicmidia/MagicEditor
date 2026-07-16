"""Memory-mapped file source for large documents (stub)."""

from __future__ import annotations

from pathlib import Path

# Threshold from architecture: files larger than this use mmap, not full RAM read.
MMAP_THRESHOLD_BYTES = 50 * 1024 * 1024


def should_use_mmap(path: Path | str, size_bytes: int | None = None) -> bool:
    """Return True when the file should be opened via mmap."""
    if size_bytes is None:
        size_bytes = Path(path).stat().st_size
    return size_bytes > MMAP_THRESHOLD_BYTES
