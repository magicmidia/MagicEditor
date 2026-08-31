"""Architecture gates for syntax / huge-file policy."""

from __future__ import annotations

SYNTAX_OFF_BYTES = 20 * 1024 * 1024
HUGE_UI_BYTES = 5 * 1024 * 1024
MMAP_BYTES = 5 * 1024 * 1024
FULL_TEXT_MAX_BYTES = 2 * 1024 * 1024
PROBE_BYTES = 64 * 1024


def syntax_enabled_for_size(size: int, *, user_enabled: bool = True) -> bool:
    """Architecture: disable full-file lexers above 20 MB."""
    if not user_enabled:
        return False
    return int(size) <= SYNTAX_OFF_BYTES
