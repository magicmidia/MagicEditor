"""Quick Open file walk (service — not in UI ctor)."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

_SKIP = {".git", ".venv", "node_modules", "__pycache__", ".mypy_cache"}


def iter_workspace_files(root: Path | str, *, max_files: int = 2000) -> list[str]:
    base = Path(root)
    if not base.is_dir():
        return []
    out: list[str] = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in _SKIP]
        for name in filenames:
            out.append(str(Path(dirpath) / name))
            if len(out) >= max_files:
                return out
    return out


def walk_workspace(root: Path | str) -> Iterator[str]:
    yield from iter_workspace_files(root)
