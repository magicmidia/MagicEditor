"""Performance dashboard metrics (no fake cloud sync)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any


@dataclass
class PerformanceSnapshot:
    python: str
    platform: str
    line_count: int
    buffer_bytes: int
    huge_mode: bool
    mmap_active: bool
    gpu_hint: str
    portable: bool
    spell_enabled: bool

    def as_lines(self) -> list[str]:
        return [
            f"Python: {self.python}",
            f"Platform: {self.platform}",
            f"Lines: {self.line_count}",
            f"Buffer: {self.buffer_bytes} bytes",
            f"Huge mode: {'yes' if self.huge_mode else 'no'}",
            f"mmap: {'yes' if self.mmap_active else 'no'}",
            f"GPU: {self.gpu_hint}",
            f"Portable: {'yes' if self.portable else 'no'}",
            f"Spell: {'on' if self.spell_enabled else 'off'}",
        ]


def snapshot_for_document(
    *,
    line_count: int,
    buffer_bytes: int,
    huge_mode: bool,
    mmap_active: bool,
    gpu_acceleration: bool,
    portable: bool,
    spell_enabled: bool,
) -> PerformanceSnapshot:
    return PerformanceSnapshot(
        python=sys.version.split()[0],
        platform=sys.platform,
        line_count=line_count,
        buffer_bytes=buffer_bytes,
        huge_mode=huge_mode,
        mmap_active=mmap_active,
        gpu_hint="enabled" if gpu_acceleration else "software",
        portable=portable,
        spell_enabled=spell_enabled,
    )


def document_mmap_active(doc: Any) -> bool:
    return getattr(doc, "_mmap", None) is not None
