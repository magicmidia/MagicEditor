"""Compare-file I/O with size cap (out of UI)."""

from __future__ import annotations

from pathlib import Path

COMPARE_CAP_BYTES = 2_000_000


def read_compare_text(path: Path | str, *, cap: int = COMPARE_CAP_BYTES) -> str:
    target = Path(path)
    if not target.is_file():
        return ""
    size = target.stat().st_size
    if size > cap * 4:
        raw = target.read_bytes()[:cap]
    else:
        raw = target.read_bytes()[:cap]
    return raw.decode("utf-8", errors="replace")
